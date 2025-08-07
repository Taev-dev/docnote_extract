from __future__ import annotations

import logging
from dataclasses import dataclass
from types import ModuleType
from typing import Annotated
from typing import Any
from typing import Literal
from typing import cast
from typing import get_origin
from typing import get_type_hints
from typing import overload

from docnote import DOCNOTE_CONFIG_ATTR
from docnote import DocnoteConfig
from docnote import DocnoteConfigParams
from docnote import Note

from docnote_extract._crossrefs import Crossref
from docnote_extract._crossrefs import Crossreffed
from docnote_extract._crossrefs import is_crossreffed
from docnote_extract._extraction import ModulePostExtraction
from docnote_extract._extraction import TrackingRegistry
from docnote_extract._types import Singleton
from docnote_extract.discovery import ModuleTreeNode
from docnote_extract.discovery import validate_config

logger = logging.getLogger(__name__)


def normalize_namespace_item(
        name_in_parent: str,
        value: Any,
        parent_annotations: dict[str, Any],
        parent_effective_config: DocnoteConfig,
        ) -> NormalizedObj:
    """Given a single item from a namespace (ie, **not a module**), this
    creates a NormalizedObj and returns it.
    """
    # Here we're associating the object with any module-level annotations,
    # but we're not yet separating the docnote annotations from the rest
    raw_annotation = parent_annotations.get(name_in_parent, Singleton.MISSING)
    normalized_annotation = normalize_annotation(raw_annotation)

    config_params: DocnoteConfigParams = \
        parent_effective_config.get_stackables()
    config_params.update(normalized_annotation.config_params)

    # All done. Filtering comes later; here we JUST want to do the
    # normalization!
    return NormalizedObj(
        obj_or_stub=value,
        annotateds=normalized_annotation.annotateds,
        effective_config=DocnoteConfig(**config_params),
        notes=normalized_annotation.notes,
        type_=normalized_annotation.type_,
        canonical_module=None,
        canonical_name=None)


@dataclass(slots=True)
class NormalizedAnnotation:
    type_: Any | Literal[Singleton.MISSING]
    notes: tuple[Note, ...]
    config_params: DocnoteConfigParams
    annotateds: tuple[LazyResolvingAnnotated, ...]


def normalize_annotation(
        annotation: Any | Literal[Singleton.MISSING]
        ) -> NormalizedAnnotation:
    """Given the annotation for a particular $thing, this extracts out
    any the type hint itself, any attached notes, config params, and
    also any additional ``Annotated`` extras.

    TODO: this also needs to normalize the type itself; the result
    should be crossreffified and just generally suitable for direct
    use in documentation generation
    """
    if annotation is Singleton.MISSING:
        return NormalizedAnnotation(
            type_=Singleton.MISSING,
            notes=(),
            config_params={},
            annotateds=())
    if is_crossreffed(annotation):
        return NormalizedAnnotation(
            type_=annotation,
            notes=(),
            config_params={},
            annotateds=())

    all_annotateds: tuple[Any, ...]
    origin = get_origin(annotation)
    if origin is Annotated:
        type_ = annotation.__origin__
        all_annotateds = annotation.__metadata__

    else:
        type_ = annotation
        all_annotateds = ()

    config_params: DocnoteConfigParams = {}

    notes: list[Note] = []
    external_annotateds = []
    for annotated in all_annotateds:
        # Note: if the note has its own config, that gets used later; it
        # doesn't modify the rest of the notes!
        if isinstance(annotated, Note):
            notes.append(annotated)
        elif isinstance(annotation, DocnoteConfig):
            config_params.update(annotation.as_nontotal_dict())
        else:
            external_annotateds.append(annotation)

    return NormalizedAnnotation(
        type_=type_,
        notes=tuple(notes),
        config_params=config_params,
        annotateds=tuple(external_annotateds))


# Ugh, normalization is always more complicated than it needs to be.
def normalize_module_dict(  # noqa: C901, PLR0912
        module: ModulePostExtraction,
        module_tree: Annotated[
                ModuleTreeNode,
                Note('''Note that this needs to be the ^^full^^ firstparty
                    module tree, and not just the node for the current module!
                    ''')]
        ) -> dict[str, NormalizedObj]:
    from_annotations: dict[str, Any] = get_type_hints(
        module, include_extras=True)
    dunder_all: set[str] = set(getattr(module, '__all__', ()))
    retval: dict[str, NormalizedObj] = {}

    for name, obj in module.__dict__.items():
        canonical_module, canonical_name = _get_or_infer_canonical_origin(
            name,
            obj,
            tracking_registry=module._docnote_extract_import_tracking_registry,
            containing_module=module.__name__,
            containing_dunder_all=dunder_all,
            containing_annotation_names=set(from_annotations))

        # Here we're associating the object with any module-level annotations,
        # but we're not yet separating the docnote annotations from the rest
        raw_annotation = from_annotations.get(
            name, Singleton.MISSING)
        if raw_annotation is Singleton.MISSING:
            all_annotateds = ()
            type_ = raw_annotation
        else:
            origin = get_origin(raw_annotation)
            if origin is Annotated:
                type_ = raw_annotation.__origin__
                all_annotateds = raw_annotation.__metadata__
            else:
                type_ = raw_annotation
                all_annotateds = ()

        # Here we're starting to construct an effective config for the object.
        # Note that this is kinda unseparable from the next part, since we're
        # iterating over all of the annotations and separating them out into
        # docnote-vs-not. I mean, yes, we could actually carve this out into
        # a separate function, but it would be more effort than it's worth.
        config_params: DocnoteConfigParams
        if canonical_module is Singleton.UNKNOWN or canonical_module is None:
            config_params = {}
        else:
            # Remember that we're checking EVERYTHING in the module right now,
            # including things we've imported, so this might be outside the
            # firstparty tree. Therefore, we need a fallback here.
            try:
                canonical_module_node = module_tree.find(canonical_module)
            except (KeyError, ValueError):
                config_params = {}
            else:
                config_params = (
                    canonical_module_node.effective_config.get_stackables())

        # This gets any config that was attrached via decorator, for classes
        # and functions.
        if hasattr(obj, DOCNOTE_CONFIG_ATTR):
            config_params.update(
                getattr(obj, DOCNOTE_CONFIG_ATTR).as_nontotal_dict())

        # Now finally we're looking on the annotations themselves. Typically
        # these are module-level variables.
        notes: list[Note] = []
        external_annotateds = []
        for annotation in all_annotateds:
            # Note: if the note has its own config, that gets used later; it
            # doesn't modify the rest of the notes!
            if isinstance(annotation, Note):
                notes.append(annotation)
            elif isinstance(annotation, DocnoteConfig):
                config_params.update(annotation.as_nontotal_dict())
            else:
                external_annotateds.append(annotation)

        # All done. Filtering comes later; here we JUST want to do the
        # normalization!
        retval[name] = NormalizedObj(
            obj_or_stub=obj,
            annotateds=tuple(external_annotateds),
            effective_config=DocnoteConfig(**config_params),
            notes=tuple(notes),
            type_=type_,
            canonical_module=canonical_module,
            canonical_name=canonical_name)

    return retval


def _get_or_infer_canonical_origin(
        name_in_containing_module: str,
        obj: Any,
        *,
        tracking_registry: TrackingRegistry,
        containing_module: str,
        containing_dunder_all: set[str],
        containing_annotation_names: set[str]
        ) -> tuple[
            str | Literal[Singleton.UNKNOWN] | None,
            str | Literal[Singleton.UNKNOWN] | None]:
    """Call this on a module member to retrieve its __module__
    attribute, as well as the name it was assigned within that module,
    or to try and infer the canonical source of the object when no
    __module__ attribute is available.
    """
    if isinstance(obj, ModuleType):
        return None, None

    if is_crossreffed(obj):
        metadata = obj._docnote_extract_metadata
        if metadata.traversals:
            logger.warning(
                'Canonical source not inferred due to traversals on module '
                + 'attribute. %s:%s -> %s',
                containing_module, name_in_containing_module, metadata)
            return Singleton.UNKNOWN, Singleton.UNKNOWN

        return metadata.module_name, metadata.toplevel_name

    # Do this next. This allows us more precise tracking of non-stubbed objects
    # that are imported from a re-exported location. In other words, we want
    # the import location to be canonical, and would prefer to have that rather
    # than the definition location, which is what we would get from
    # ``__module__`` and ``__name__`.
    canonical_from_registry = tracking_registry.get(id(obj), None)
    # Note that the None could be coming EITHER from the default in the above
    # .get(), OR because we had multiple conflicting references to it, and we
    # therefore can't use the registry to infer its location.
    if canonical_from_registry is not None:
        return canonical_from_registry

    canonical_module, canonical_name = _get_dunder_module_and_name(obj)
    if canonical_module is None:
        if (
            # Summary:
            # ++  not imported from a tracking module
            # ++  no ``__module__`` attribute
            # ++  name contained within ``__all__``
            # Conclusion: assume it's a canonical member.
            name_in_containing_module in containing_dunder_all
            # Summary:
            # ++  not imported from a tracking module (or at least not uniquely
            #     so) -- therefore, either a reftype or an actual value
            # ++  no ``__module__`` attribute
            # ++  name contained within **module annotations**
            # Conclusion: assume it's a canonical member. This is almost
            # guaranteed; otherwise you'd have to annotate something you just
            # imported
            or name_in_containing_module in containing_annotation_names
        ):
            canonical_module = containing_module
            canonical_name = name_in_containing_module

        else:
            canonical_module = Singleton.UNKNOWN
            canonical_name = Singleton.UNKNOWN

    # Purely here to be defensive.
    elif canonical_name is None:
        raise RuntimeError(
            'Impossible branch! ``__module__`` detected without ``__name__``!')

    return canonical_module, canonical_name


def _get_dunder_module_and_name(
        obj: Any
        ) -> tuple[str, str] | tuple[None, None]:
    """So, things are a bit more complicated than simply getting the
    ``__module__`` attribute of an object and using it. The problem is
    that INSTANCES of a class will inherit its ``__module__`` value.
    This causes problems with... well, basically everything ^^except^^
    classes, functions, methods, descriptors, and generators that are
    defined within the module being inspected.

    I thought about trying to import the ``__module__`` and then
    comparing the actual ``obj`` against ``__module__.__name__``, but
    that's a whole can of worms.

    Instead, we're simply limiting the ``__module__`` value to only
    return something if the ``__name__`` is also defined. This should
    limit it to only the kinds of objects that don't cause problems.
    """
    canonical_name = getattr(obj, '__name__', None)
    if canonical_name is None:
        return None, None
    else:
        return obj.__module__, canonical_name


@dataclass(slots=True)
class NormalizedObj:
    """This is a normalized representation of an object. It contains the
    (stubbed) runtime value of the object along with any annotateds
    (from ``Annotated``), as well as the unpacked-from-``Annotated``
    type itself.
    """
    obj_or_stub: Annotated[
            Any,
            Note('''This is the actual runtime value of the object. It might
                be a ``RefType`` stub or an actual object.''')]
    notes: tuple[Note, ...]
    effective_config: Annotated[
            DocnoteConfig,
            Note('''This contains the end result of all direct configs on the
                object, layered on top of any stackable config items from
                parent scope(s).''')]
    annotateds: tuple[object, ...]
    type_: Annotated[
            Any | Literal[Singleton.MISSING],
            Note('''This might be a literal value, as is the case with
                builtins and nostub modules. It might also be a ``RefType``
                stub. Or it could be some combination thereof, depending on
                how the nostub import cascade plays out.

                Or, of course, it could just be missing!''')]

    # Where the value was declared. String if known (because it had a
    # __module__ or it had a docnote). None if not applicable, because the
    # object isn't a direct child of a module.
    canonical_module: str | Literal[Singleton.UNKNOWN] | None
    # What name the object had in the module it was declared. String if
    # known, None if not applicable.
    canonical_name: str | Literal[Singleton.UNKNOWN] | None

    def __post_init__(self):
        validate_config(
            self.effective_config,
            f'Object effective config for {self.obj_or_stub} '
            + f'({self.canonical_module=}, {self.canonical_name=})')


@dataclass(slots=True, frozen=True, kw_only=True)
class LazyResolvingAnnotated:
    _ref_metadata: Crossref

    def __call__(self) -> Any:
        """Resolves the actual annotation. Note that the import hook
        must be uninstalled **before** calling this!
        """
        raise NotImplementedError

    @overload
    @classmethod
    def from_annotated(cls, annotated: Crossreffed) -> LazyResolvingAnnotated:
        ...
    @overload
    @classmethod
    def from_annotated[T](cls, annotated: T) -> T: ...
    @classmethod
    def from_annotated[T](
            cls,
            annotated: T | Crossreffed
            ) -> T | LazyResolvingAnnotated:
        """Converts a reftype-based ``Annotated[]`` member into a
        ``LazyResolvingAnnotated`` instance. If the member was not
        a reftype, returns the value back.

        TODO: this should recurse into containers.
        """
        if is_crossreffed(annotated):
            return cls(_ref_metadata=annotated._docnote_extract_metadata)
        else:
            # This is necessary because we're using TypeGuard instead of
            # TypeIs so that we can have pseudo-intersections.
            return cast(T, annotated)
