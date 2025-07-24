from __future__ import annotations

import importlib
import logging
import sys
import typing
from collections.abc import Generator
from collections.abc import Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from dataclasses import field
from functools import partial
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

UNPURGEABLE_MODULES: Annotated[
        set[str],
        Note('''As noted in the stdlib documentation for the ``sys`` module,
            removing certain modules from ``sys.modules`` can create problems.
            If you run into such issues, you can add the problem module to
            this set to prevent it from being removed. In that case, any time
            the stub status changes, it will be reloaded instead of removed.
            ''')
    ] = set()
_THIRDPARTY_BYPASS_PACKAGES = {
    'docnote',
    'docnote_extract',
}
_METACLASS_MARKERS: set[RefMetadata] = {
    RefMetadata(module='configatron', name='ConfigMeta', traversals=()),
}
_MANUAL_BYPASS_PACKAGES: ContextVar[frozenset[str]] = ContextVar(
    '_MANUAL_BYPASS_PACKAGES', default=frozenset())
_MANUAL_METACLASS_MARKERS: ContextVar[frozenset[RefMetadata]] = ContextVar(
    '_MANUAL_METACLASS_MARKERS', default=frozenset())
_MODULE_TO_INSPECT: ContextVar[str] = ContextVar('_MODULE_TO_INSPECT')

_ALT_IMPORT_RECURSION_GUARD: ContextVar[frozenset[str]] = ContextVar(
    '_ALT_IMPORT_RECURSION_GUARD', default=frozenset())
_TRACKER_BYPASS_PACKAGES: ContextVar[frozenset[str]] = ContextVar(
    '_TRACKER_BYPASS_PACKAGES', default=frozenset())

logger = logging.getLogger(__name__)


@contextmanager
def bypass_stubbing(*module_names: str):
    """This contextmanager/decorator can be used as an escape hatch to
    force a group of exact module names (ex, ``('foo.bar', 'foo.baz')``
    are not included in ``('foo',)``) to skip the import stubbing.

    In this case, the import metadata will be determined by its
    ``__module__`` and ``__name__`` attributes; if either of these is
    missing, the result will be an unknown reference.

    Use this if you run into problems with a particular dependency not
    working with the import stubbing. The downsides are:
    ++  docs extraction will take longer. If the module has import side
        effects, that can be substantial
    ++  depending on the specifics of the un-stubbed module, it can
        result in a cascade of bypasses for its dependencies, and then
        their dependencies, and so on
    ++  it requires that module to be available within the virtualenv
        used for docs generation
    ++  extracted references to objects from the un-stubbed module will
        point to the module where the object was defined, which isn't
        always the same as where the object was imported from. This can
        result in broken reference names and links
    ++  module-level constants won't work, as they lack ``__module__``
        and/or ``__name__``.
    ++  you may run into issues with ``if typing.TYPE_CHECKING`` blocks.
    """
    stacked_bypass = frozenset({
        *_MANUAL_BYPASS_PACKAGES.get(), *module_names})
    ctx_token = _MANUAL_BYPASS_PACKAGES.set(stacked_bypass)
    try:
        yield
    finally:
        _MANUAL_BYPASS_PACKAGES.reset(ctx_token)


@contextmanager
def use_metaclass_reftype(*object_qualnames: str):
    """This contextmanager/decorator can be used as an escape hatch to
    force the import hook to create a ``Reftype`` instance that can be
    used as a metaclass. This allows you to continue to use the normal
    import hook, even when you depend on (or yourself author) libraries
    that make use of metaclasses.

    Pass values as a fully-qualified name, for example: ``foo.bar:Baz``
    would mark the ``Bar`` class in the ``foo.bar`` module as a
    metaclass.
    """
    refs: list[RefMetadata] = []
    for object_qualname in object_qualnames:
        module, _, name = object_qualname.partition(':')
        if not name:
            raise ValueError(
                'use_metaclass_reftype requires a qualname! (ex ``foo:Bar``)',
                object_qualname)

        refs.append(RefMetadata(module=module, name=name, traversals=()))

    stacked_markers = frozenset({
        *_MANUAL_METACLASS_MARKERS.get(), *refs})
    ctx_token = _MANUAL_METACLASS_MARKERS.set(stacked_markers)
    try:
        yield
    finally:
        _MANUAL_METACLASS_MARKERS.reset(ctx_token)


@contextmanager
def inspect_module(module_name: str) -> Generator[ModuleType, None, None]:
    """This contextmanager ensures that you get a normal module instance
    for the ``module_name`` you want to inspect, while all other
    non-bypassed, non-stdlib modules are passed through the import hook.

    Note that the module name here must be an EXACT module fullname.
    This doesn't work for entire packages (deliberately!), it only does
    singular modules.
    """
    if _MODULE_TO_INSPECT.get(None) is not None:
        raise RuntimeError('inspect_module is not reentrant!', module_name)
    importlib.invalidate_caches()

    ctx_token = _MODULE_TO_INSPECT.set(module_name)
    try:
        # This means we have a hooked/stubbed version of the library already
        # present, and we need to reload it.
        # In most cases, this should be equivalent to deleting the module from
        # sys.modules, and then calling ``import_module``, but we can just let
        # importlib handle all of our dirty work.
        if module_name in sys.modules:
            real_fake_module = importlib.reload(sys.modules[module_name])
        # In this case, we don't have a hooked/stubbed version of the library,
        # but we still need to load it in the first place.
        else:
            real_fake_module = importlib.import_module(module_name)

        try:
            yield real_fake_module

        # To avoid cross-pollination, we want to make sure that we don't keep
        # the real_fake version of the module around in sys modules, since
        # the next module to be inspected won't then get our reference proxies,
        # but rather, actual objects.
        # Note that this only affects the actual module being inspected; it
        # has no bearing on other modules that were only imported BECAUSE of
        # the module being inspected. (These will already be stubbed anyways.)
        finally:
            if module_name in UNPURGEABLE_MODULES:
                # Note that this is necessary to un-bypass the import hook.
                # We could structure this differently, probably with an
                # exitstack, but the logic would be way more complicated to
                # follow. This is an easy and understandable workaround.
                _MODULE_TO_INSPECT.set('')
                importlib.reload(real_fake_module)

            else:
                del sys.modules[module_name]

    finally:
        _MODULE_TO_INSPECT.reset(ctx_token)


class _StubbingFinderLoader(Loader):
    """This is an import finder/loader that creates a normal module
    object and populates its __getattr__ with a function that simply
    returns a mock-style object.

    This is useful to be able to use importlib.import_library on a
    source file without having any of its upstream dependencies
    installed. It also helps us keep track of the object provenance,
    making it easier to figure out exactly which objects were defined in
    which modules, even if they lack a __module__ attribute.
    """
    stubbed_modules: set[str]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stubbed_modules = set()

    def find_spec(
            self,
            fullname: str,
            path: Sequence[str] | None,
            target: ModuleType | None = None
            ) -> ModuleSpec | None:
        """We use find_spec to filter which packages we're going to
        install the import hook for, and which we aren't.
        """
        base_package, *_ = fullname.split('.')
        in_stdlib = None
        in_3p_bypass = None
        in_manual_bypass = None
        in_recursion_guard = None
        # Note: keep this in sync with is_stubbed!
        if (
            # Note that base_package is correct here; sys.stdlib_module_names
            # only includes the toplevel package
            (in_stdlib := base_package in sys.stdlib_module_names)
            or (in_3p_bypass := base_package in _THIRDPARTY_BYPASS_PACKAGES)
            or (in_manual_bypass := fullname in _MANUAL_BYPASS_PACKAGES.get())
            or (
                in_recursion_guard :=
                    fullname in _ALT_IMPORT_RECURSION_GUARD.get())
        ):
            logger.debug(
                'Bypassing stub for module %s. (in_stdlib: %s, '
                + 'in_3p_bypass: %s, in_manual_bypass: %s, '
                + 'in_recursion_guard: %s)',
                fullname, in_stdlib, in_3p_bypass, in_manual_bypass,
                in_recursion_guard)
            return None

        # This is how we bypass our loader for individual modules that we want
        # to inspect
        current_target_module = _MODULE_TO_INSPECT.get(None)
        if current_target_module is None or current_target_module != fullname:
            logger.debug('Will return stub spec: %s', fullname)
            self.stubbed_modules.add(fullname)
            return ModuleSpec(fullname, self)

        # When loading the current_target_module, we need to have some special
        # logic; see docstring in _find_alt_spec.
        else:
            logger.debug(
                'Finding alt spec for module_to_inspect: %s', fullname)
            alt_spec = self._find_alt_spec(fullname, path, target)

            if alt_spec is None:
                logger.warning(
                    'No alt spec for module_to_inspect (%s); submodules will '
                    + 'fail to import.', fullname)

                return None

            else:
                return ModuleSpec(
                    fullname,
                    self,
                    loader_state=alt_spec)

    def create_module(self, spec: ModuleSpec) -> None | ModuleType:
        if spec.loader_state is None:
            logger.debug(
                'Using default module machinery for stubbed module: %s',
                spec.name)
            return None

        else:
            # Note that we already checked this to be non-None in
            # _find_alt_spec, before accepting it as a match
            delegated_state = cast(
                _DelegatedLoaderState,
                spec.loader_state)
            alt_module = delegated_state.alt_loader.create_module(
                spec.loader_state)

            if alt_module is None:
                logger.debug(
                    'Using default module machinery for delegated stubbed '
                    + 'module: %s', spec.name)
                return None

            else:
                logger.debug(
                    'Using created module from delegated loader: %s',
                    spec.name)
                alt_module.__spec__ = spec
                return alt_module

    def exec_module(self, module: ModuleType):
        """The import system creates a module object for us; in
        ``exec_module``, it's our job to populate the module with its
        namespace.

        However, instead of populating the module with actual objects,
        we'll just give it a MODULE ``__getattr__`` that creates proxy
        objects on the fly.

        The exception is if we need to actually inspect the module; in
        that case, we delegate the exec to the alt loader.
        """
        spec = getattr(module, '__spec__', None)
        if (
            spec is not None
            and isinstance(spec.loader_state, _DelegatedLoaderState)
        ):
            logger.debug(
                'Delegating module exec for module under inspection: %s',
                spec.loader_state.fullname)
            # This allows us to also get references hidden behind circular
            # imports
            typing.TYPE_CHECKING = True
            try:
                spec.loader_state.alt_loader.exec_module(module)
            finally:
                typing.TYPE_CHECKING = False

        else:
            logger.debug('Stubbing module: %s', module.__name__)
            module.__getattr__ = partial(
                _stubbed_getattr, module_name=module.__name__)
            module.__path__ = []

    def _find_alt_spec(
            self,
            fullname: str,
            path: Sequence[str] | None,
            target: ModuleType | None = None
            ) -> _DelegatedLoaderState | None:
        """So here's the deal. When we're loading the module to inspect,
        we can't simply return None and let the rest of the import
        machinery handle it. The problem is that the import machinery
        is just a bit too smart: if we're in a submodule, and we
        return None, then it just stops searching. In other words, it's
        operating under the assumption that a submodule can never exist
        at a different loader than the parent module -- which is usually
        a great assumption.

        Furthermore, for (some unknown reason), if you try and get an
        alternate spec by more-or-less replicating the normal import
        logic, the whole thing doesn't work. What does work, is to
        temporarily remove all of the parent modules and do a fresh
        import call while bypassing the module to inspect and all of
        its parents.

        You might think we could then just use this module directly,
        but unfortunately, that's incorrect; it might contain imports
        from its parent modules, which would be temporarily un-stubbed.
        So instead, we scavenge the spec from that loaded module,
        restore all of the temporarily-patched-out parent module stubs,
        and proceed with our special loading process using a
        _DelegatedLoaderState.

        The other reason this is necessary is that we need to
        selectively enable typing.TYPE_CHECKING -- but only when we get
        around to the actual module we need to check, during its
        ``exec_module`` call (otherwise we'd run into import loops).
        """
        # First of all, we want to patch all of the parent modules outside of
        # sys.modules. This appears to interfere with discovery otherwise.
        popped_modules = {}
        module_segments = fullname.split('.')
        parent_module_names = [
            '.'.join(module_segments[:index + 1])
            for index in range(len(module_segments) - 1)]
        for parent_module_name in parent_module_names:
            if parent_module_name in sys.modules:
                popped_modules[parent_module_name] = sys.modules.pop(
                    parent_module_name)

        try:
            with _alt_import_recursion_guard(*parent_module_names, fullname):
                alt_loaded_module = importlib.import_module(fullname)

            alt_spec = alt_loaded_module.__spec__
            if alt_spec is None or alt_spec.loader is None:
                logger.warning(
                    'Alt loaded module had empty spec; will break! %s',
                    fullname)
                return None

            else:
                return _DelegatedLoaderState(
                    fullname=fullname,
                    alt_loader=alt_spec.loader,
                    alt_spec=alt_spec)

        finally:
            # We can't just overwrite, in case one of the parent modules was
            # for some reason missing. Theoretically impossible, but we're
            # being extremely defensive here.
            for parent_module_name in parent_module_names:
                sys.modules.pop(parent_module_name, None)
            # Critical! Otherwise the loader will short-circuit with the
            # temp module we just loaded.
            sys.modules.pop(fullname, None)

            sys.modules.update(popped_modules)


class _WrapWithTrackerFinderLoader(Loader):
    """This is an import finder/loader that first allows the rest of the
    finder/loaders to load a module, and then wraps the resulting module
    object in an intermediate that tracks the ID of every object
    imported from every wrapped module, and then returns the original
    object.

    This allows us to keep track of where, exactly, objects were
    imported from (which is not necessarily the same as where they were
    defined!), even if they were not stubbed.

    The only exception here is the stdlib, because this relies upon us
    being able to manipulate sys.modules relatively freely, which can't
    be done with the stdlib without causing stability issues.
    """
    # This is a sort of... parallel version of sys.modules. In addition to the
    # purging when uninstalling the import hook (via the keys), this also
    # allows us to avoid having a bazillion copies of the alt modules. NOTE
    # THAT THE VALUES ARE NOT WRAPPED! These are the original, unwrapped
    # modules, hot-off-the-press.
    wrapped_alt_modules: dict[str, _WrappedTrackingModule]
    # This, meanwhile, is the thing responsible for keeping track of the
    # actual imports. The format is module_fullname, attr_name. If None,
    # that means that it encountered multiple DIFFERENT source for the object
    # ID, and therefore, it can't be used to determine provenance anymore.
    registry: dict[int, tuple[str, str] | None]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wrapped_alt_modules = {}
        self.registry = {}

    def find_spec(
            self,
            fullname: str,
            path: Sequence[str] | None,
            target: ModuleType | None = None
            ) -> ModuleSpec | None:
        """We use find_spec to filter which packages we're going to
        install the import hook for, and which we aren't.
        """
        base_package, *_ = fullname.split('.')

        if base_package in sys.stdlib_module_names:
            logger.debug(
                'Bypassing tracker wrapping for stdlib module %s.', fullname)
            return None

        if base_package in _THIRDPARTY_BYPASS_PACKAGES:
            logger.debug(
                'Bypassing tracker wrapping for %s via hard-coded third party '
                + 'bypass package %s',
                fullname, base_package)
            return None

        if fullname in _TRACKER_BYPASS_PACKAGES.get():
            logger.debug(
                'Bypassing tracker wrapping via context for %s.', fullname)
            return None

        # We can always skip these, since this will only be a temporary module
        # for the purposes of calculating a spec.
        if fullname in _ALT_IMPORT_RECURSION_GUARD.get():
            logger.debug(
                'Bypassing tracker wrapping via recursion guard for %s.',
                fullname)
            return None

        alt_spec = self._find_alt_spec(fullname, path, target)

        if alt_spec is None:
            logger.warning(
                'No alt spec for wrapped module (%s). Reverting to '
                + 'other loaders.', fullname)
            return None

        else:
            return ModuleSpec(
                fullname,
                self,
                loader_state=alt_spec)

    def _find_alt_spec(
            self,
            fullname: str,
            path: Sequence[str] | None,
            target: ModuleType | None = None
            ) -> _DelegatedLoaderState | None:
        """This is very similar to the stubber's _find_alt_spec. The
        primary difference is that we keep track of all of the original
        module objects instead of discarding them. This ensures that we
        have a consistent set of modules (and therefore a consistent
        set of objects), which makes sure that their IDs are also,
        therefore, consistent.
        """
        # First of all, we want to patch all of the parent modules outside of
        # sys.modules. This appears to interfere with discovery otherwise.
        popped_modules = {}
        module_segments = fullname.split('.')

        parent_modules = [
            '.'.join(module_segments[:index + 1])
            for index in range(len(module_segments) - 1)]
        modules_to_swap = {*parent_modules}
        modules_to_swap.update(self.wrapped_alt_modules)

        for module_to_swap in modules_to_swap:
            if module_to_swap in sys.modules:
                popped_modules[module_to_swap] = sys.modules.pop(
                    module_to_swap)

            if module_to_swap in self.wrapped_alt_modules:
                sys.modules[module_to_swap] = self.wrapped_alt_modules[
                    module_to_swap]

        try:
            with _alt_import_recursion_guard(*modules_to_swap, fullname):
                alt_loaded_module = importlib.import_module(fullname)

            alt_spec = alt_loaded_module.__spec__
            if alt_spec is None or alt_spec.loader is None:
                return None

            else:
                return _DelegatedLoaderState(
                    fullname=fullname,
                    alt_loader=alt_spec.loader,
                    alt_spec=alt_spec)

        finally:
            # Note that we might have added more of these in the meantime,
            # if there were other imports of wrapped modules while importing
            # the alt versions
            modules_to_unswap = {*parent_modules}
            modules_to_unswap.update(self.wrapped_alt_modules)
            for module_to_unswap in modules_to_unswap:
                sys.modules.pop(module_to_unswap, None)
            # Critical! Otherwise the loader will short-circuit with the
            # temp module we just loaded.
            sys.modules.pop(fullname, None)

            sys.modules.update(popped_modules)

    def create_module(self, spec: ModuleSpec) -> None | ModuleType:
        """We have to do a little bit of black magic here; we need to
        keep the alt loader's version of the module, and it needs to be
        the thing that actually gets exec'd by the alt loader. However,
        we simultaneously need to have importlib construct a separate
        module object for us to use as the proxying module.
        """
        if spec.loader_state is None:
            logger.warning(
                'Missing loader state for wrapped module; will break!: %s',
                spec.name)
            return None

        else:
            delegated_state = cast(_DelegatedLoaderState, spec.loader_state)
            alt_module = delegated_state.alt_loader.create_module(
                spec.loader_state)

            if alt_module is None:
                logger.debug(
                    'Using default module machinery for delegated wrapped '
                    + 'module: %s', spec.name)
                alt_module = ModuleType(spec.name)
                alt_module.__name__ = spec.name
                alt_module.__loader__ = spec.loader_state.alt_loader
                alt_module.__spec__ = spec

        spec.loader_state.alt_module = alt_module
        return None

    def exec_module(self, module: ModuleType):
        """Here, we first have the alt loader finalize the real version
        of the module, using all of the alt values on the loader state.
        Then, we wrap that into our own module object, setting both the
        canonical module as a private attribute there, as well as the
        getattr method that is responsible for tracking anything
        accessing members of the module.
        """
        spec = getattr(module, '__spec__', None)
        if (
            spec is None
            or not isinstance(spec.loader_state, _DelegatedLoaderState)
        ):
            logger.warning(
                'Missing spec for wrapped module during exec; will break! %s',
                module.__name__)
            return

        alt_module = spec.loader_state.alt_module
        spec.loader_state.alt_loader.exec_module(alt_module)
        logger.debug('Wrapping module w/ tracking proxy: %s', module.__name__)
        module.__getattr__ = partial(
            _wrapped_tracking_getattr,
            module_name=module.__name__,
            registry=self.registry,
            src_module=alt_module)
        module.__path__ = []
        # The ignore here is so we can set the attr value without pyright
        # complaining. After that, we can use the typeguard.
        module._docnote_extract_src_module = alt_module  # type: ignore


def _wrapped_tracking_getattr(
        name: str,
        *,
        module_name: str,
        registry: dict[int, tuple[str, str] | None],
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
    src_object = getattr(src_module, name)
    obj_id = id(src_object)
    tracked_src = (module_name, name)

    existing_record = registry.get(obj_id, Singleton.MISSING)
    if existing_record is Singleton.MISSING:
        registry[obj_id] = tracked_src

    # Note: we only need to overwrite if it isn't already none; otherwise we
    # can just skip it. None is a sink state, a black hole.
    elif existing_record is not None and existing_record != tracked_src:
        registry[obj_id] = None

    return src_object


@dataclass(slots=True)
class _DelegatedLoaderState:
    """We use this partly as a container for ``loader_state``, and
    partly as a way to easily detect that a module was created via the
    delegated/alt path.
    """
    fullname: str
    alt_loader: Loader
    alt_spec: ModuleSpec
    alt_module: ModuleType = field(init=False)


def _stubbed_getattr(name: str, *, module_name: str):
    """Okay, yes, we could create our own module type. Alternatively,
    we could just inject a module.__getattr__!

    This replaces every attribute access (regardless of whether or not
    it exists on the true source module; we're relying upon type
    checkers to ensure that) with a reftype.
    """
    to_reference = RefMetadata(
        module=module_name, name=name, traversals=())

    in_shared_markers = None
    in_manual_markers = None
    if (
        (in_shared_markers := to_reference in _METACLASS_MARKERS)
        or (in_manual_markers :=
                to_reference in _MANUAL_METACLASS_MARKERS.get())
    ):
        logger.debug(
            'Returning metaclass reftype for %s. (in_shared_markers: %s, '
            + 'in_manual_markers: %s)',
            to_reference, in_shared_markers, in_manual_markers)
        return make_metaclass_reftype(module=module_name, name=name)

    else:
        logger.debug('Returning normal reftype for %s', to_reference)
        return make_reftype(module=module_name, name=name)


def install_import_hook():
    # TODO: support bypasses via params to ``install_import_hook`` in addition
    # to context managers, and limit context managers to advanced usage (eg
    # testing)
    importlib.invalidate_caches()
    # A bit suboptimal that we need to completely re-index the list twice in
    # a row, but whatever. Note that the order here is important; we need the
    # stubber ahead of the tracker, so we do the tracker first and then
    # the stubber, so the stubber bumps the tracker out of first place.
    sys.meta_path.insert(0, _WrapWithTrackerFinderLoader())
    sys.meta_path.insert(0, _StubbingFinderLoader())


def uninstall_import_hook():
    """As you might guess by the name, this removes any installed import
    hook. Note that it is safe to call this multiple times, and
    regardless of whether or not an import hook has been installed; in
    those cases, it will simply be a no-op.

    What is not immediately obvious from the name, however, is that this
    **will also force reloading of every stubbed module loaded by the
    import hook.** Therefore, after calling ``uninstall_import_hook``,
    you should be reverted to a clean slate.
    """
    target_indices = []
    for index, meta_path_finder in enumerate(sys.meta_path):
        if isinstance(
            meta_path_finder,
            (_StubbingFinderLoader, _WrapWithTrackerFinderLoader)
        ):
            target_indices.append(index)

    modules_to_remove: set[str] = set()
    # By reversing, we don't need to worry about offsets from deleting stuff
    for index in reversed(target_indices):
        meta_path_finder = cast(
            _StubbingFinderLoader | _WrapWithTrackerFinderLoader,
            sys.meta_path.pop(index))

        if isinstance(meta_path_finder, _StubbingFinderLoader):
            modules_to_remove.update(meta_path_finder.stubbed_modules)
        else:
            modules_to_remove.update(meta_path_finder.wrapped_alt_modules)

    for module_to_remove in modules_to_remove:
        module_obj = sys.modules.get(module_to_remove)
        if module_obj is not None:
            if module_to_remove in UNPURGEABLE_MODULES:
                importlib.reload(module_obj)
            else:
                del sys.modules[module_to_remove]


@contextmanager
def stubbed_imports() -> Generator[None, None, None]:
    """A contextmanager / decorator to temporarily apply the import
    hook. Intended primarily for use in our own test code, but might
    be useful for anyone wanting to create their own post-processing
    system for extracted docs.
    """
    install_import_hook()
    try:
        yield
    finally:
        uninstall_import_hook()


def is_stubbed(module_name: str) -> bool:
    """Returns True if the passed module is stubbed (presuming the
    import hook is active; otherwise, it returns True if the passed
    module ^^would be^^ stubbed, provided the import hook were
    subsequently activated).
    """
    root_package_name, _, _ = module_name.partition('.')
    return not (
        root_package_name in sys.stdlib_module_names
        or root_package_name in _THIRDPARTY_BYPASS_PACKAGES
        or module_name in _MANUAL_BYPASS_PACKAGES.get()
        or module_name == _MODULE_TO_INSPECT.get(None))


@contextmanager
def _alt_import_recursion_guard(*module_names):
    """We use this while getting the alt spec for the module to inspect,
    to prevent infinite recursion while loading the real-fake version of
    the module (and its parents).
    """
    stacked_bypass = frozenset({
        *_ALT_IMPORT_RECURSION_GUARD.get(), *module_names})
    ctx_token = _ALT_IMPORT_RECURSION_GUARD.set(stacked_bypass)
    try:
        yield
    finally:
        _ALT_IMPORT_RECURSION_GUARD.reset(ctx_token)


def get_tracking_registry_snapshot() -> dict[int, tuple[str, str] | None]:
    """Retrieves a snapshto of the tracking registry from any installed
    _WrapWithTrackerFinderLoader instances.
    """
    retval = {}
    for meta_path_finder in sys.meta_path:
        if isinstance(meta_path_finder, _WrapWithTrackerFinderLoader):
            if retval:
                raise RuntimeError(
                    'Multiple tracking registries not supported')

            retval.update(meta_path_finder.registry)
    return retval


def is_wrapped_tracking_module(
        module: ModuleType
        ) -> TypeGuard[_WrappedTrackingModule]:
    return (
        isinstance(module, ModuleType)
        and hasattr(module, '_docnote_extract_src_module'))


class _WrappedTrackingModuleBase(Protocol):
    _docnote_extract_src_module: ModuleType


class _WrappedTrackingModule(ModuleType, _WrappedTrackingModuleBase):
    """This is really just intended for use as a pseudo-protocol, since
    protocols can't inherit from concrete base classes, but we need
    something that's the intersection between a moduletype and a
    _WrappedTrackingModuleBase.
    """
