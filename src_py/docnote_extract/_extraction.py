from __future__ import annotations

import logging
import sys
import typing
from collections.abc import Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import KW_ONLY
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from functools import partial
from importlib import import_module
from importlib import reload as reload_module
from importlib.abc import Loader
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import Annotated
from typing import Any
from typing import Protocol
from typing import TypeGuard
from typing import cast

from docnote import Note

from docnote_extract._reftypes import RefMetadata
from docnote_extract._reftypes import make_metaclass_reftype
from docnote_extract._reftypes import make_reftype
from docnote_extract._types import Singleton
from docnote_extract.discovery import discover_all_modules

type TrackingRegistry = dict[int, tuple[str, str] | None]
UNPURGEABLE_MODULES: Annotated[
        set[str],
        Note('''As noted in the stdlib documentation for the ``sys`` module,
            removing certain modules from ``sys.modules`` can create problems.
            If you run into such issues, you can add the problem module to
            this set to prevent it from being removed. In that case, any time
            the stub status changes, it will be reloaded instead of removed.
            ''')
    ] = set()
# These are completely 100% untouched by our import hook.
NOHOOK_PACKAGES = {
    'docnote',
    'docnote_extract',
}
_EXTRACTION_PHASE: ContextVar[_ExtractionPhase] = ContextVar(
    '_EXTRACTION_PHASE')

_MODULE_TO_INSPECT: ContextVar[str] = ContextVar('_MODULE_TO_INSPECT')
_ACTIVE_TRACKING_REGISTRY: ContextVar[TrackingRegistry] = ContextVar(
    '_ACTIVE_TRACKING_REGISTRY')

logger = logging.getLogger(__name__)


class ReftypeMarker(Enum):
    METACLASS = 'metaclass'
    DECORATOR = 'decorator'


class _StubStrategy(Enum):
    """Slightly different than extraction phase, this determines what
    we're going to do when we get to later steps in the import process.
    """
    STUB = 'stub'
    INSPECT = 'inspect'
    TRACK = 'track'


_REFTYPE_MARKERS: ContextVar[dict[RefMetadata, ReftypeMarker]] = ContextVar(
    '_REFTYPE_MARKERS', default={  # noqa: B039
        RefMetadata(module='configatron', name='ConfigMeta', traversals=()):
            ReftypeMarker.METACLASS
    })


class _ExtractionPhase(Enum):
    """This describes exactly which phase of extraction we're in. The
    _ExtractionFinderLoader uses it to avoid recursion issues and
    dictate control flow and/or delegation to other imports.
    """
    HOOKED = 'hooked'
    EXPLORATION = 'exploration'
    EXTRACTION = 'extraction'


@dataclass(slots=True, frozen=True)
class _ExtractionFinderLoader(Loader):
    """We use this import finder/loader to power all of our docnote
    extraction.
    """
    firstparty_packages: frozenset[str]

    _: KW_ONLY
    # Note: full module name
    nostub_firstparty_modules: frozenset[str] = field(
        default_factory=frozenset)

    # Note: root package, not individual modules
    nostub_packages: Annotated[
        frozenset[str],
        Note('''Marking a package as nostub be used as an escape hatch to
            force it to skip the import stubbing. This requires the package
            to be installed within the virtualenv used for docs extraction.

            Imports from nostub modules will still be tracked, so they usually
            still provide identical or near-identical import metadata to
            stubbed modules.

            Note that this can only be done on a per-package (``foo``) and not
            per-module (``foo.bar``) basis, since otherwise we'd need to
            cascade dependency analysis into every third-party package with a
            nostub module.

            Use this if you run into problems with a particular dependency not
            working with the import stubbing. The downsides are:
            ++  docs extraction will take longer. If the module has import side
                effects, that can be substantial
            ++  depending on the specifics of the un-stubbed module, it can
                result in a cascade of bypasses for its dependencies, and then
                their dependencies, and so on
            ++  it requires that module to be available within the virtualenv
                used for docs generation
            ++  you may run into issues with ``if typing.TYPE_CHECKING`` blocks
            ++  you can very quickly run into issues with traversals. This can,
                for example, cause problems with references to imported
                ``Enum`` members

            In short, you should avoid marking packages as ``nostub`` unless
            you run into problems directly related to stubbing, which cannot be
            solved by other, more precise, escape hatches (for example, using
            ``mark_special_reftype`` to force a particular import to be a
            metaclass- or decorator-compatible stub).''')
    ] = field(default_factory=frozenset)

    module_stash_prehook: dict[str, ModuleType] = field(
        default_factory=dict, repr=False)
    # Mocking stubs. These are created lazily, as-needed, on-the-fly, whenever
    # we need one -- but as with sys.modules, once it's been created, we'll
    # return the same one, from this lookup.
    module_stash_stubbed: dict[str, ModuleType] = field(
        default_factory=dict, repr=False)
    # Internals of the module are real, but any non-bypassed third-party
    # deps are stubbed out. This is what we use for constructing specs, and
    # for modules that need real versions of objects. Note that this version
    # of it is the actual real module, NOT our tracking man-in-the-middle
    # version of the module.
    module_stash_nostub_raw: dict[str, ModuleType] = field(
        default_factory=dict, repr=False)
    # Same as above, but this is the tracked version. This is what we use
    # during inspection to keep a registry of objects that were imported from
    # a particular partial module. This will always be smaller than nostub_raw,
    # because nostub_raw includes all first-party modules, but this only
    # includes stubbed ones.
    module_stash_tracked: dict[str, ModuleType] = field(
        default_factory=dict, repr=False)
    # This is used for marking things dirty.
    inspected_modules: set[str] = field(
        default_factory=set, repr=False)

    def discover_and_extract(self) -> dict[str, ModulePostExtraction]:
        ctx_token = _EXTRACTION_PHASE.set(_ExtractionPhase.HOOKED)
        try:
            self._stash_prehook_modules()
            self.install()

            # We're relying upon the full exploration here to import all
            # possible modules needed for extraction. Then we stash the raw
            # versions of nostub- and firstparty modules, cleanup sys, and
            # move on to the next phase, where we use the raw modules.
            _EXTRACTION_PHASE.set(_ExtractionPhase.EXPLORATION)
            firstparty_names = frozenset(
                discover_all_modules(*self.firstparty_packages))
            self._stash_firstparty_or_nostub_raw()
            # We need to clean up everything here because we'll be
            # transitioning into tracked modules instead of the raw ones
            self.cleanup_sys(self._get_all_dirty_modules())

            _EXTRACTION_PHASE.set(_ExtractionPhase.EXTRACTION)

            retval: dict[str, ModulePostExtraction] = {}
            for module_name in firstparty_names:
                retval[module_name] = self.extract_firstparty(module_name)
            # Note that uninstall will handle final cleanup
            return retval

        finally:
            try:
                self.uninstall()
            finally:
                _EXTRACTION_PHASE.reset(ctx_token)
                self._unstash_prehook_modules()

    def _stash_firstparty_or_nostub_raw(self):
        """This checks sys.modules for any firstparty or nostub modules,
        adding references to them within ``module_stash_nostub_raw``.
        """
        for fullname, module in sys.modules.items():
            package_name, _, _ = fullname.partition('.')
            if (
                package_name in self.firstparty_packages
                or package_name in self.nostub_packages
            ):
                self.module_stash_nostub_raw[fullname] = module

    def extract_firstparty(
            self,
            module_name: str
            ) -> ModulePostExtraction:
        """Here, given a firstparty module name, we construct a new
        module object for it that mocks out all non-stub-bypassed
        external dependencies, regardless of first- or third-party.

        We've structured this to go on a per-module basis to make
        unit tests easier.
        """
        # This is important because we're trying to avoid cleaning up all of
        # sys.modules for every module to extract. Instead, we just force a
        # reload of this particular module.
        sys.modules.pop(module_name, None)
        import_tracking_registry: TrackingRegistry = {}
        inspect_ctx_token = _MODULE_TO_INSPECT.set(module_name)
        try:
            with _activatate_tracking_registry(import_tracking_registry):
                extracted_module = cast(
                    ModulePostExtraction, import_module(module_name))

            extracted_module._docnote_extract_import_tracking_registry = (
                import_tracking_registry)
            return extracted_module
        finally:
            _MODULE_TO_INSPECT.reset(inspect_ctx_token)
            # We don't really need to clean up ALL of sys.modules, just the
            # module we inspected. Everything else will get cleaned up during
            # uninstallation.
            # Note: the None here is because we might have run into an error
            # importing something, and therefore not (yet) have added it to
            # sys.modules.
            sys.modules.pop(module_name, None)

    def install(self) -> None:
        """Installs the loader in sys.meta_path and then gets everything
        ready for discovery.
        """
        for finder in sys.meta_path:
            if isinstance(finder, _ExtractionFinderLoader):
                raise RuntimeError(
                    'Cannot have multiple active extraction loaders!')

        sys.meta_path.insert(0, self)

    @classmethod
    def uninstall(cls) -> None:
        """As you might guess by the name, this removes any installed
        import hook. Note that it is safe to call this multiple times,
        and regardless of whether or not an import hook has been
        installed; in those cases, it will simply be a no-op.

        What is not immediately obvious from the name, however, is that
        this **will also force reloading of every stubbed module loaded
        by the import hook.** Therefore, after calling``uninstall``,
        you should be reverted to a clean slate.
        """
        """DON'T FORGET THAT YOU NEED TO PURGE EVERY IMPORT FROM ALL
        OF THE LOOKUPS FROM sys.modules!!!
        """
        # In theory, we only have one of these -- install() won't allow
        # multiples -- but we want to be extra defensive here (and also,
        # idempotent!)
        target_indices = []
        for index, meta_path_finder in enumerate(sys.meta_path):
            if isinstance(meta_path_finder, cls):
                target_indices.append(index)

        modules_to_remove: set[str] = set()
        # By reversing, we don't need to worry about offsets from deleting
        # stuff in case we somehow have multiples
        for index in reversed(target_indices):
            meta_path_finder = cast(
                _ExtractionFinderLoader,
                sys.meta_path.pop(index))

            modules_to_remove.update(meta_path_finder._get_all_dirty_modules())

        cls.cleanup_sys(modules_to_remove)

    @classmethod
    def cleanup_sys(cls, modules_to_remove: set[str]) -> None:
        """Given a list of module names, removes them from sys.modules,
        unless they're unpurgeable, in which case we force a reload.
        """
        # Note that we don't need to worry about importlib.invalidate_caches,
        # because we're not changing the actual content of the modules, just
        # the environment they're exec'd into.
        for module_to_remove in modules_to_remove:
            module_obj = sys.modules.get(module_to_remove)
            if module_obj is not None:
                if module_to_remove in UNPURGEABLE_MODULES:
                    reload_module(module_obj)
                else:
                    del sys.modules[module_to_remove]

    def _get_all_dirty_modules(self) -> set[str]:
        """Get a snapshot set of every single module that might be dirty
        at the finder/loader. Use this to clean sys.modules when
        transitioning between phases.
        """
        modules: set[str] = set()
        modules.update(self.module_stash_stubbed)
        modules.update(self.module_stash_nostub_raw)
        modules.update(self.module_stash_tracked)
        modules.update(self.inspected_modules)
        return modules

    def _get_firstparty_dirty_modules(self) -> set[str]:
        """Same as above, but limited just to the firstparty modules.
        Use this between inspecting individual firstparty modules.
        """
        retval: set[str] = set()
        all_modules = self._get_all_dirty_modules()
        for module in all_modules:
            pkg_name, _, _ = module.partition('.')
            if pkg_name in self.firstparty_packages:
                retval.add(module)

        return retval

    def _stash_prehook_modules(self):
        """This checks all of sys.modules, stashing and removing
        anything that isn't stdlib or a thirdparty bypass package.
        """
        prehook_module_names = sorted(sys.modules)
        for prehook_module_name in prehook_module_names:
            package_name, _, _ = prehook_module_name.partition('.')

            if (
                package_name not in sys.stdlib_module_names
                and package_name not in NOHOOK_PACKAGES
            ):
                logger.info('Stashing prehook module %s', prehook_module_name)

                # This is purely to save us needing to reimport the package
                # to build out a raw package for use during the exploration
                # phase. The only difference is that we're not popping it;
                # we're JUST stashing it so it can be restored after
                # uninstalling the import hook.
                if (
                    package_name in self.nostub_packages
                    or package_name in self.firstparty_packages
                ):
                    prehook_module = sys.modules[prehook_module_name]

                else:
                    logger.debug(
                        'Popping %s from sys.modules for stash',
                        prehook_module_name)
                    prehook_module = sys.modules.pop(prehook_module_name)

                self.module_stash_prehook[prehook_module_name] = prehook_module

    def _unstash_prehook_modules(self):
        for name, module in self.module_stash_prehook.items():
            logger.info('Restoring prehook module %s', name)
            sys.modules[name] = module

    def find_spec(
            self,
            fullname: str,
            path: Sequence[str] | None,
            target: ModuleType | None = None
            ) -> ModuleSpec | None:
        """This determines:
        ++  whether or not we're going to load a package at all
        ++  what strategy we're going to take for loading
        etc.
        """
        base_package, *_ = fullname.split('.')

        # Note that base_package is correct here; stdlib doesn't add in
        # every submodule.
        if base_package in sys.stdlib_module_names:
            logger.debug('Bypassing wrapping for stdlib module %s.', fullname)
            return None
        if base_package in NOHOOK_PACKAGES:
            logger.debug(
                'Bypassing tracker wrapping for %s via hard-coded third party '
                + 'nohook package %s',
                fullname, base_package)
            return None

        # Thirdparty packages not marked with nostub will ALWAYS return a
        # stub package as long as the import hook is installed, regardless of
        # extraction phase. Otherwise, we'd need them to be installed in the
        # docs virtualenv, reftypes would never be generated, etc etc etc.
        if (
            base_package not in self.firstparty_packages
            and base_package not in self.nostub_packages
        ):
            logger.debug('Will return stub spec for %s', fullname)
            # We don't need any loader state here; we're just going to stub it
            # completely, so we can simply return a plain spec.
            return ModuleSpec(
                name=fullname,
                loader=self,
                loader_state=_ExtractionLoaderState(
                    fullname=fullname,
                    is_firstparty=False,
                    stub_strategy=_StubStrategy.STUB))

        # All of the rest of our behavior depends upon our current
        # extraction phase.
        else:
            phase = _EXTRACTION_PHASE.get()
            if phase is _ExtractionPhase.EXPLORATION:
                # During exploration, we defer all non-stubbed importing
                # to the rest of the finder/loaders. This is then stashed
                # before re-cleaning sys.modules, so that we can harvest the
                # raw specs for delegated loading.
                return None

            elif phase is _ExtractionPhase.EXTRACTION:
                return self._get_delegated_spec(
                    base_package, fullname, path, target)

            else:
                logger.warning(
                    'Import %s during invalid extraction phase %s will be '
                    + 'neither hooked nor tracked. You may encounter import '
                    + 'errors. This is almost certainly a bug.',
                    fullname, phase)
                return None

    def _get_delegated_spec(
            self,
            base_package: str,
            fullname: str,
            path: Sequence[str] | None,
            target: ModuleType | None
            ) -> ModuleSpec | None:
        """Delegated specs are ones where we need the other
        finder/loaders to do the actual importing, but we need to first
        manipulate the import environment in some way, or wrap the
        resulting module.
        """
        module_to_inspect = _MODULE_TO_INSPECT.get()
        # Note: ordering here is important. The inspection needs to happen
        # first, because you might have a nostub firstparty module under
        # inspection, and we need to short-circuit the other checks.
        if fullname == module_to_inspect:
            stub_strategy = _StubStrategy.INSPECT
        elif (
            fullname in self.nostub_firstparty_modules
            or base_package in self.nostub_packages
        ):
            stub_strategy = _StubStrategy.TRACK
        else:
            stub_strategy = _StubStrategy.STUB

        # Here we can reuse the already-calculated spec from the
        # thirdparty_stubbed phase, we just need to replace the
        # tracking registry and stub strategy
        existing_spec = self.module_stash_nostub_raw[fullname].__spec__
        if existing_spec is None or existing_spec.loader is None:
            logger.warning(
                'No existing spec for delegated module during extraction; '
                + 'tracking and stubbing will fail! %s', fullname)
            return None

        return ModuleSpec(
            name=fullname,
            loader=self,
            loader_state=_DelegatedLoaderState(
                fullname=fullname,
                is_firstparty=base_package in self.firstparty_packages,
                delegated_loader=existing_spec.loader,
                delegated_spec=existing_spec,
                stub_strategy=stub_strategy))

    def create_module(self, spec: ModuleSpec) -> None | ModuleType:
        """What we do here depends on the stubbing strategy for the
        module.

        If we're going to ``_StubbingStrategy.STUB`` the module, we
        don't need to do anything special; we can just return None and
        allow normal semantics to happen.

        Otherwise, though, we're going to delegate the loading to a
        different finder/loader, which means we need to do a bit of
        black magic. We need to keep the delegated loader's version of
        the module, and that then, in turn, needs to be the thing that's
        actually used in the ^^delegated^^ ``exec_module``. However, we
        internally need to preserve our own **separate** module object
        for use as the wrapper, which we then use for our own
        ``exec_module``.
        """
        loader_state = spec.loader_state
        if not isinstance(loader_state, _ExtractionLoaderState):
            logger.warning(
                'Missing loader state for %s. This is almost certainly a bug, '
                + 'and may cause stuff to break.', spec.name)
            return None

        if loader_state.stub_strategy is _StubStrategy.STUB:
            if loader_state.fullname in self.module_stash_stubbed:
                logger.debug(
                    'Using cached stub module for %s', loader_state.fullname)
                loader_state.from_stash = True
                return self.module_stash_stubbed[loader_state.fullname]

            else:
                logger.debug(
                    'Using default module machinery for stubbed module: %s',
                    loader_state.fullname)

        else:
            if not isinstance(loader_state, _DelegatedLoaderState):
                logger.warning(
                    'Delegated ``_StubStrategy`` without '
                    + '``_DelegatedLoaderState``! Tracking and/or inspection '
                    + 'will break for %s.', loader_state.fullname)

            else:
                # We don't have a stash for inspected modules (because they're
                # only used once).
                if loader_state.fullname in self.module_stash_tracked:
                    logger.debug(
                        'Using cached tracking module for %s',
                        loader_state.fullname)
                    loader_state.from_stash = True
                    return self.module_stash_tracked[loader_state.fullname]

                # Since the stubbing status of the rest of the firstparty
                # package tree will have changed, we need to re-create any
                # firstparty tracked modules (in addition to the inspection
                # ones, which are always firstparty).
                if loader_state.is_firstparty:
                    delegated_loader = loader_state.delegated_loader
                    delegated_module = delegated_loader.create_module(
                        spec.loader_state)

                    if delegated_module is None:
                        logger.debug(
                            'Using default module machinery for delegated '
                            + 'wrapped module: %s', spec.name)
                        delegated_module = ModuleType(spec.name)
                        delegated_module.__name__ = spec.name
                        delegated_module.__loader__ = delegated_loader
                        delegated_module.__spec__ = spec

                    loader_state.delegated_module = delegated_module

                # Note that non-firstparty tracked packages can always just
                # use the default machinery, because we're just going to grab
                # the stashed module for the target, and not recreate it.

    def exec_module(self, module: ModuleType):
        """Ah, at long last: the final step of the import process.
        We have a module object ready to go and a spec with a
        ``loader_state``, which itself contains a ``stub_strategy``
        telling us what to do. From here on out, it's smooth sailing.

        If we see ``_StubbingStrategy.STUB``, then we're going to just
        add a module-level ``__getattr__`` that creates proxy objects
        on the fly, do a bit of other bookkeeping, and return the
        resulting module. Easy peasy.

        The other two stubbing strategies are a bit more interesting.
        In both cases, we're reliant upon already having established
        the actual module during the exploration phase, which is
        retrieved within ``_get_delegated_spec``.

        In the ``TRACK`` strategy, we need to first let the delegated
        loader ``exec_module`` on its prepared module object from
        ``create_module``. We then wrap this into a tracking module.

        In both of those cases, we need to remember to cache the
        resulting object (and check the ``from_stash`` attribute to
        potentially bypass loading ``exec`` entirely).

        In the ``INSPECT`` strategy, we again let the delegated loader
        ``exec_module`` on its prepared module object. However here, we
        neither cache the module itself (since we only inspect each
        module once), nor do we wrap it. We also don't have to worry
        about setting the tracking registry; this is done within
        ``extract_firstparty``. There is one thing we need to do though:
        we do need to make sure to add the module name to
        ``self.inspected_modules``, so we're absolutely sure
        it gets cleaned up during uninstallation.
        """
        spec = getattr(module, '__spec__', None)
        if (
            spec is None
            or not isinstance(spec.loader_state, _ExtractionLoaderState)
        ):
            logger.error(
                'Missing spec for delegated or stubbed module %s during '
                + '``exec_module``. Will noop; expect import errors!',
                module.__name__)
            return

        loader_state = spec.loader_state
        # We don't need to do anything when returning stashed modules; they've
        # already been populated.
        if loader_state.from_stash:
            return

        if loader_state.stub_strategy is _StubStrategy.STUB:
            logger.debug('Stubbing module: %s', module.__name__)
            module.__getattr__ = partial(
                _stubbed_getattr, module_name=module.__name__)
            module.__path__ = []
            self.module_stash_stubbed[loader_state.fullname] = module

        elif isinstance(loader_state, _DelegatedLoaderState):
            if loader_state.stub_strategy is _StubStrategy.TRACK:
                logger.debug(
                    'Wrapping module w/ tracking proxy: %s',
                    loader_state.fullname)
                module = cast(WrappedTrackingModule, module)
                # Firstparty tracking needs to re-exec'd, because the stub
                # state of other firstparty modules has changed.
                if loader_state.is_firstparty:
                    delegated_module = loader_state.delegated_module
                    loader_state.delegated_loader.exec_module(delegated_module)
                # Otherwise, we can just grab the module from the raw stash.
                else:
                    delegated_module = self.module_stash_nostub_raw[
                        loader_state.fullname]

                module.__getattr__ = partial(
                    _wrapped_tracking_getattr,
                    module_name=module.__name__,
                    src_module=delegated_module)
                module.__path__ = []
                module._docnote_extract_src_module = delegated_module
                self.module_stash_tracked[loader_state.fullname] = module

            # Note: no caching here; we only inspect modules a single time.
            elif loader_state.stub_strategy is _StubStrategy.INSPECT:
                # However, we do need to keep track of this for cleanup
                # purposes!
                self.inspected_modules.add(loader_state.fullname)
                logger.debug(
                    'Delegating module exec for module under inspection: %s',
                    loader_state.fullname)
                # This allows us to also get references hidden behind circular
                # imports
                typing.TYPE_CHECKING = True
                try:
                    loader_state.delegated_loader.exec_module(module)
                finally:
                    typing.TYPE_CHECKING = False

            else:
                logger.error(
                    'Unknown stub strategy for delegated module %s during '
                    + '``exec_module``! Will noop; expect import errors!',
                    loader_state.fullname)
                return

        else:
            logger.error(
                'Wrong loader state type for delegated or stubbed module %s '
                + 'during ``exec_module``. Will noop; expect import errors!',
                loader_state.fullname)
            return


@contextmanager
def _activatate_tracking_registry(registry: TrackingRegistry):
    """This sets up a fresh tracking registry for use during extraction.

    Note that we use a different one of these for every time we load a
    firstparty module, because we want to be as precise as possible with
    avoiding duplicate constants (for example, multiple modules using
    bools).
    """
    if _ACTIVE_TRACKING_REGISTRY.get(None) is not None:
        raise RuntimeError(
            'Cannot have multiple activated tracking registries!')

    ctx_token = _ACTIVE_TRACKING_REGISTRY.set(registry)
    try:
        yield
    finally:
        _ACTIVE_TRACKING_REGISTRY.reset(ctx_token)


@dataclass(slots=True, kw_only=True)
class _ExtractionLoaderState:
    fullname: str
    is_firstparty: bool
    stub_strategy: _StubStrategy
    from_stash: bool = False


@dataclass(slots=True, kw_only=True)
class _DelegatedLoaderState(_ExtractionLoaderState):
    """We use this partly as a container for ``loader_state``, and
    partly as a way to easily detect that a module was created via the
    delegated/alt path.
    """
    delegated_loader: Loader
    delegated_spec: ModuleSpec
    delegated_module: ModuleType = field(init=False)


def _wrapped_tracking_getattr(
        name: str,
        *,
        module_name: str,
        src_module: ModuleType
        ) -> Any:
    """Okay, yes, we could create our own module type. Alternatively,
    we could just inject a module.__getattr__!

    This returns the original object from the src_module, but before
    doing so, it records the module name and attribute name within
    the registry.

    If we encounter a repeated import of the same object, but with a
    different source, then we overwrite the registry value with None to
    indicate that we no longer know definitively where the object came
    from.
    """
    registry = _ACTIVE_TRACKING_REGISTRY.get(None)
    src_object = getattr(src_module, name)
    obj_id = id(src_object)
    tracked_src = (module_name, name)

    if registry is not None:
        # We use None to indicate that there's a conflict within the retrieval
        # imports we've encountered, so we can't use it as a stand-in for
        # missing stuff.
        existing_record = registry.get(obj_id, Singleton.MISSING)
        if existing_record is Singleton.MISSING:
            registry[obj_id] = tracked_src

        # Note: we only need to overwrite if it isn't already none; otherwise
        # we can just skip it. None is a sink state, a black hole.
        elif existing_record is not None and existing_record != tracked_src:
            registry[obj_id] = None

    return src_object


def _stubbed_getattr(name: str, *, module_name: str):
    """Okay, yes, we could create our own module type. Alternatively,
    we could just inject a module.__getattr__!

    This replaces every attribute access (regardless of whether or not
    it exists on the true source module; we're relying upon type
    checkers to ensure that) with a reftype.
    """
    to_reference = RefMetadata(module=module_name, name=name, traversals=())
    special_markers = _REFTYPE_MARKERS.get()

    special_reftype = special_markers.get(to_reference)
    if special_reftype is None:
        logger.debug('Returning normal reftype for %s', to_reference)
        return make_reftype(module=module_name, name=name)

    elif special_reftype is ReftypeMarker.METACLASS:
        logger.debug('Returning metaclass reftype for %s.', to_reference)
        return make_metaclass_reftype(module=module_name, name=name)

    else:
        # This is just blocked on having a decorator flavor added to
        # reftypes. Should be straightforward, but I want to limit the scope
        # of the current code push to just a refactor.
        raise NotImplementedError(
            'Other special metaclass reftypes not yet supported.')


@contextmanager
def mark_special_reftype(markers: dict[RefMetadata, ReftypeMarker]):
    """This contextmanager/decorator can be used as an escape hatch to
    force the import hook to create a special ``Reftype`` instance that
    can, for example, be used as a metaclass. This allows you to
    continue to use import stubs, even when you depend on (or yourself
    author) libraries that make use of metaprogramming techniques that
    would otherwise break reftypes.
    """
    for ref in markers:
        if ref.traversals:
            # The problem here is that we need to update the whole reftype
            # creation process. This needs to get injected right at the call
            # to ``make_reftype`` if we're going to support traversals,
            # or something. It gets complicated quickly.
            raise NotImplementedError(
                'Traversals not yet supported for special reftypes.')

    stacked_markers = {**_REFTYPE_MARKERS.get(), **markers}
    ctx_token = _REFTYPE_MARKERS.set(stacked_markers)
    try:
        yield
    finally:
        _REFTYPE_MARKERS.reset(ctx_token)


def is_wrapped_tracking_module(
        module: ModuleType
        ) -> TypeGuard[WrappedTrackingModule]:
    return (
        isinstance(module, ModuleType)
        and hasattr(module, '_docnote_extract_src_module'))


class _WrappedTrackingModuleBase(Protocol):
    _docnote_extract_src_module: ModuleType


class WrappedTrackingModule(ModuleType, _WrappedTrackingModuleBase):
    """This is really just intended for use as a pseudo-protocol, since
    protocols can't inherit from concrete base classes, but we need
    something that's the intersection between a moduletype and a
    WrappedTrackingModuleBase.
    """


class _ModulePostExtractionBase(Protocol):
    _docnote_extract_import_tracking_registry: TrackingRegistry


class ModulePostExtraction(ModuleType, _ModulePostExtractionBase):
    """This is really just intended for use as a pseudo-protocol, since
    protocols can't inherit from concrete base classes, but we need
    something that's the intersection between a moduletype and a
    ModulePostExtractionBase.
    """


def is_module_post_extraction(
        module: ModuleType
        ) -> TypeGuard[ModulePostExtraction]:
    return (
        isinstance(module, ModuleType)
        and hasattr(module, '_docnote_extract_import_tracking_registry'))
