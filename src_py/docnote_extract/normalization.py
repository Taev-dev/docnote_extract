from __future__ import annotations

import logging
from dataclasses import dataclass
from types import ModuleType
from typing import Annotated
from typing import Any
from typing import Literal
from typing import get_origin
from typing import get_type_hints

from docnote_extract._reftypes import is_reftyped
from docnote_extract._types import Singleton
from docnote_extract.import_hook import get_tracking_registry_snapshot

logger = logging.getLogger(__name__)


def normalize_module_dict(module: ModuleType) -> dict[str, NormalizedObj]:
    from_annotations: dict[str, Any] = get_type_hints(
        module, include_extras=True)
    dunder_all: set[str] = set(getattr(module, '__all__', ()))
    retval: dict[str, NormalizedObj] = {}

    for name, obj in module.__dict__.items():
        canonical_module, canonical_name = _get_or_infer_canonical_origin(
            name,
            obj,
            containing_module=module.__name__,
            containing_dunder_all=dunder_all,
            containing_annotation_names=set(from_annotations))

        raw_annotation = from_annotations.get(
            name, Singleton.MISSING)
        if raw_annotation is Singleton.MISSING:
            annotations = ()
            type_ = raw_annotation
        else:
            origin = get_origin(raw_annotation)
            if origin is Annotated:
                type_ = raw_annotation.__origin__
                annotations = raw_annotation.__metadata__
            else:
                type_ = raw_annotation
                annotations = ()

        retval[name] = NormalizedObj(
            obj_or_stub=obj,
            annotations=annotations,
            type_=type_,
            canonical_module=canonical_module,
            canonical_name=canonical_name)

    return retval


def _get_or_infer_canonical_origin(
        name_in_containing_module: str,
        obj: Any,
        *,
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
    registry_snapshot = get_tracking_registry_snapshot()
    canonical_from_registry = registry_snapshot.get(id(obj), None)
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
    obj_or_stub: Any
    annotations: tuple[Any, ...]
    type_: Any | Literal[Singleton.MISSING]

    # Where the value was declared. String if known (because it had a
    # __module__ or it had a docnote). None if not applicable, because the
    # object isn't a direct child of a module.
    canonical_module: str | Literal[Singleton.UNKNOWN] | None
    # What name the object had in the module it was declared. String if
    # known, None if not applicable.
    canonical_name: str | Literal[Singleton.UNKNOWN] | None
