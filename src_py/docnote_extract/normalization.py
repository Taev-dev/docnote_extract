from __future__ import annotations

import logging
from dataclasses import dataclass
from types import ModuleType
from typing import Annotated
from typing import Any
from typing import Literal
from typing import get_origin
from typing import get_type_hints

from docnote import DocnoteConfig
from docnote import DocnoteConfigParams
from docnote import Note

from docnote_extract._extraction import ModulePostExtraction
from docnote_extract._extraction import TrackingRegistry
from docnote_extract._reftypes import is_reftyped
from docnote_extract._types import Singleton

logger = logging.getLogger(__name__)


def normalize_module_dict(
        module: ModulePostExtraction
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

        raw_annotation = from_annotations.get(
            name, Singleton.MISSING)
        if raw_annotation is Singleton.MISSING:
            all_annotations = ()
            type_ = raw_annotation
        else:
            origin = get_origin(raw_annotation)
            if origin is Annotated:
                type_ = raw_annotation.__origin__
                all_annotations = raw_annotation.__metadata__
            else:
                type_ = raw_annotation
                all_annotations = ()

        config_params: DocnoteConfigParams = {}
        notes: list[Note] = []
        external_annotations = []
        for annotation in all_annotations:
            if isinstance(annotation, Note):
                notes.append(annotation)
                if annotation.config is not None:
                    config_params.update(annotation.config.as_nontotal_dict())
            elif isinstance(annotation, DocnoteConfig):
                config_params.update(annotation.as_nontotal_dict())
            else:
                external_annotations.append(annotation)

        retval[name] = NormalizedObj(
            obj_or_stub=obj,
            annotations=tuple(external_annotations),
            config=DocnoteConfig(**config_params),
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

    if is_reftyped(obj):
        metadata = obj._docnote_extract_metadata
        if metadata.traversals:
            logger.warning(
                'Canonical source not inferred due to traversals on module '
                + 'attribute. %s:%s -> %s',
                containing_module, name_in_containing_module, metadata)
            return Singleton.UNKNOWN, Singleton.UNKNOWN

        return metadata.module, metadata.name

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

    canonical_module = getattr(obj, '__module__', None)
    if canonical_module is None:
        if (
            name_in_containing_module in containing_dunder_all
            or name_in_containing_module in containing_annotation_names
        ):
            canonical_module = containing_module

        else:
            canonical_module = Singleton.UNKNOWN

    canonical_name = getattr(obj, '__name__', None)
    if canonical_name is None:
        if canonical_module == containing_module:
            canonical_name = name_in_containing_module
        else:
            canonical_name = Singleton.UNKNOWN

    return canonical_module, canonical_name


@dataclass(slots=True)
class NormalizedObj:
    """This is a normalized representation of an object. It contains the
    (stubbed) runtime value of the object along with any annotations
    (from ``Annotated``), as well as the unpacked-from-``Annotated``
    type itself.
    """
    obj_or_stub: Annotated[
            Any,
            Note('''This is the actual runtime value of the object. It might
                be a ``RefType`` stub or an actual object.''')]
    notes: tuple[Note, ...]
    config: Annotated[
            DocnoteConfig,
            Note('''This contains the end result of all direct configs on the
                object. It does not, however, merge in any config values from
                parent scopes. Therefore, this must be combined with the
                stackables in parent scopes to result in the final effective
                config for the object.''')]
    annotations: tuple[Any, ...]
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
