from __future__ import annotations

import inspect
import itertools
import logging
from collections.abc import Callable
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Annotated
from typing import Any
from typing import Protocol
from typing import cast
from typing import get_overloads
from typing import get_type_hints

from docnote import DOCNOTE_CONFIG_ATTR
from docnote import DocnoteConfig
from docnote import DocnoteConfigParams
from docnote import Note

from docnote_extract._crossrefs import Crossref
from docnote_extract._crossrefs import GetattrTraversal
from docnote_extract._crossrefs import ParamTraversal
from docnote_extract._crossrefs import SignatureTraversal
from docnote_extract._crossrefs import has_crossreffed_base
from docnote_extract._crossrefs import has_crossreffed_metaclass
from docnote_extract._crossrefs import is_crossreffed
from docnote_extract._extraction import ModulePostExtraction
from docnote_extract._module_tree import ConfiguredModuleTreeNode
from docnote_extract._types import CallableColor
from docnote_extract._types import CallableDesc
from docnote_extract._types import ClassDesc
from docnote_extract._types import CrossrefDesc
from docnote_extract._types import DescBase
from docnote_extract._types import DescMetadataFactoryProtocol
from docnote_extract._types import DescMetadataProtocol
from docnote_extract._types import MethodType
from docnote_extract._types import ModuleDesc
from docnote_extract._types import ObjClassification
from docnote_extract._types import ParamDesc
from docnote_extract._types import ParamStyle
from docnote_extract._types import RetvalDesc
from docnote_extract._types import SignatureDesc
from docnote_extract._types import Singleton
from docnote_extract._types import VariableDesc
from docnote_extract._utils import extract_docstring
from docnote_extract._utils import textify_notes
from docnote_extract.normalization import LazyResolvingValue
from docnote_extract.normalization import NormalizedObj
from docnote_extract.normalization import TypeSpec
from docnote_extract.normalization import normalize_annotation
from docnote_extract.normalization import normalize_namespace_item

logger = logging.getLogger(__name__)

_desc_factories: dict[type[DescBase], _DescFactoryProtocol] = {}
def _desc_factory[T: DescBase](
        desc_type: type[T]
        ) -> Callable[[_DescFactoryProtocol[T]], _DescFactoryProtocol[T]]:
    """Second-order decorator for declaring a description factory."""
    def decorator(func: _DescFactoryProtocol[T]) -> _DescFactoryProtocol[T]:
        recast = cast(_DescFactoryAttrProto, func)
        recast._desc_factory_type = desc_type
        _desc_factories[desc_type] = func
        return func

    return decorator


class _DescFactoryAttrProto(Protocol):
    _desc_factory_type: type[DescBase]


class _DescFactoryProtocol[T: DescBase](Protocol):

    def __call__(
            self,
            name_in_parent: str,
            parent_crossref_namespace: dict[str, Crossref],
            obj: NormalizedObj,
            classification: ObjClassification,
            *,
            module_globals: dict[str, Any],
            in_class: bool = False,
            desc_metadata_factory: DescMetadataFactoryProtocol,
            ) -> T:
        """Given an object and its classification, construct a
        description instance, populating it with any required children.
        """
        ...


@dataclass(slots=True, init=False)
class DescMetadata(DescMetadataProtocol):
    """The default implementation for summary description metadata.
    """
    extracted_inclusion: bool | None
    canonical_module: str | None
    to_document: bool
    disowned: bool
    crossref_namespace: dict[str, Crossref]

    @classmethod
    def factory(
            cls,
            *,
            classification: ObjClassification | None,
            desc_class: type[DescBase],
            crossref: Crossref | None,
            annotateds: tuple[LazyResolvingValue, ...],
            metadata: dict[str, Any]
            ) -> DescMetadata:
        return cls()


def summarize_module[T: DescMetadataProtocol](
        module: ModulePostExtraction,
        normalized_objs: Annotated[
                dict[str, NormalizedObj],
                Note('All module members, with no filters applied.')],
        module_tree: ConfiguredModuleTreeNode,
        desc_metadata_factory:
            DescMetadataFactoryProtocol[T] = DescMetadata.factory
        ) -> ModuleDesc[T]:
    """For the passed post-extraction module, iterates across all
    normalized_objs and extracts their descriptions, returning them
    combined into a single ``ModuleDesc``.
    """
    module_crossref = Crossref(
        module_name=module.__name__,
        toplevel_name=None)
    namespace = _prepare_attr_namespace(module_crossref, None, normalized_objs)

    module_members = set()
    for name, normalized_obj in normalized_objs.items():
        classification = ObjClassification.from_obj(normalized_obj.obj_or_stub)
        desc_class = classification.get_desc_class()
        # This seems, at first glance, to be weird. Like, how can we have a
        # module here? Except if you do ``import foo``... welp, now you have
        # a module object!
        if classification.is_module:
            crossref = module_crossref / GetattrTraversal(name)
            module_members.add(CrossrefDesc(
                name=name,
                crossref=crossref,
                src_crossref=Crossref(
                    module_name=normalized_obj.obj_or_stub.__name__,
                    toplevel_name=None,
                    traversals=()),
                typespec=normalized_obj.typespec,
                notes=textify_notes(
                    normalized_obj.notes, normalized_obj.effective_config),
                ordering_index=normalized_obj.effective_config.ordering_index,
                child_groups=
                    normalized_obj.effective_config.child_groups or (),
                parent_group_name=
                    normalized_obj.effective_config.parent_group_name,
                metadata=desc_metadata_factory(
                    classification=classification,
                    desc_class=CrossrefDesc,
                    crossref=crossref,
                    annotateds=tuple(
                        LazyResolvingValue.from_annotated(annotated)
                        for annotated in normalized_obj.annotateds),
                    metadata=normalized_obj.effective_config.metadata or {})))

        elif desc_class is not None:
            factory = _desc_factories[desc_class]
            module_members.add(factory(
                name,
                namespace,
                normalized_obj,
                classification,
                desc_metadata_factory=desc_metadata_factory,
                module_globals=module.__dict__))

    config = module_tree.find(module.__name__).effective_config
    metadata = desc_metadata_factory(
        classification=ObjClassification.from_obj(module),
        desc_class=ModuleDesc,
        crossref=module_crossref,
        annotateds=(),
        metadata=config.metadata or {})
    metadata.extracted_inclusion = config.include_in_docs
    metadata.crossref_namespace = namespace
    metadata.canonical_module = module.__name__

    if (raw_dunder_all := getattr(module, '__all__', None)) is not None:
        dunder_all = frozenset(raw_dunder_all)
    else:
        dunder_all = None

    desc = ModuleDesc(
        crossref=module_crossref,
        name=module.__name__,
        ordering_index=config.ordering_index,
        parent_group_name=None,
        child_groups=config.child_groups or (),
        metadata=metadata,
        dunder_all=dunder_all,
        docstring=extract_docstring(module, config),
        members=frozenset(module_members))
    return desc


@_desc_factory(CrossrefDesc)
def create_crossref_desc(
        name_in_parent: str,
        parent_crossref_namespace: dict[str, Crossref],
        obj: NormalizedObj,
        classification: ObjClassification,
        *,
        module_globals: dict[str, Any],
        in_class: bool = False,
        desc_metadata_factory: DescMetadataFactoryProtocol,
        ) -> CrossrefDesc:
    """Given an object and its classification, construct a
    description instance, populating it with any required children.
    """
    src_obj = obj.obj_or_stub
    # Note: this cannot have traversals, or it would have been classified
    # as a VariableDesc instead of a re-export.
    if not is_crossreffed(src_obj):
        raise TypeError(
            'Impossible branch: re-export from non-reftype!', obj)

    crossref = parent_crossref_namespace[name_in_parent]
    metadata = desc_metadata_factory(
        classification=classification,
        desc_class=ModuleDesc,
        crossref=crossref,
        annotateds=tuple(
            LazyResolvingValue.from_annotated(annotated)
            for annotated in obj.annotateds),
        metadata=obj.effective_config.metadata or {})
    metadata.include_in_docs_as_configured = \
        obj.effective_config.include_in_docs
    metadata.crossref_namespace = parent_crossref_namespace
    metadata.canonical_module = (
        obj.canonical_module if obj.canonical_module is not Singleton.UNKNOWN
        else None)

    return CrossrefDesc(
        name=name_in_parent,
        src_crossref=src_obj._docnote_extract_metadata,
        typespec=obj.typespec,
        notes=textify_notes(obj.notes, obj.effective_config),
        crossref=crossref,
        ordering_index=obj.effective_config.ordering_index,
        child_groups=obj.effective_config.child_groups or (),
        parent_group_name=obj.effective_config.parent_group_name,
        metadata=metadata)


@_desc_factory(VariableDesc)
def create_variable_desc(
        name_in_parent: str,
        parent_crossref_namespace: dict[str, Crossref],
        obj: NormalizedObj,
        classification: ObjClassification,
        *,
        module_globals: dict[str, Any],
        in_class: bool = False,
        desc_metadata_factory: DescMetadataFactoryProtocol,
        ) -> VariableDesc:
    """Given an object and its classification, construct a
    description instance, populating it with any required children.
    """
    src_obj = obj.obj_or_stub

    # For this to be a VariableDesc and not a re-export, this must have
    # traversals.
    if is_crossreffed(src_obj):
        # I'm punting on this for now just because I need to make progress
        # and it's a huge can of worms. But one big challenge is going to
        # be eg instances of an imported type.
        raise NotImplementedError(
            'Traversals not yet supported for crossref variables',
            src_obj)

    crossref = parent_crossref_namespace[name_in_parent]
    metadata = desc_metadata_factory(
        classification=classification,
        desc_class=ModuleDesc,
        crossref=crossref,
        annotateds=tuple(
            LazyResolvingValue.from_annotated(annotated)
            for annotated in obj.annotateds),
        metadata=obj.effective_config.metadata or {})
    metadata.include_in_docs_as_configured = \
        obj.effective_config.include_in_docs
    metadata.crossref_namespace = parent_crossref_namespace
    metadata.canonical_module = (
        obj.canonical_module if obj.canonical_module is not Singleton.UNKNOWN
        else None)

    # If missing, use the runtime type as an inference -- unless the
    # object was a bare annotation (without a typespec?! weird), then
    # we can't do anything.
    if obj.typespec is None and src_obj is not Singleton.MISSING:
        typespec = TypeSpec.from_typehint(type(src_obj))
    else:
        typespec = obj.typespec

    return VariableDesc(
        name=name_in_parent,
        typespec=typespec,
        notes=textify_notes(obj.notes, obj.effective_config),
        crossref=crossref,
        ordering_index=obj.effective_config.ordering_index,
        child_groups=obj.effective_config.child_groups or (),
        parent_group_name=obj.effective_config.parent_group_name,
        metadata=metadata)


@_desc_factory(ClassDesc)
def create_class_desc(
        name_in_parent: str,
        parent_crossref_namespace: dict[str, Crossref],
        obj: NormalizedObj,
        classification: ObjClassification,
        *,
        module_globals: dict[str, Any],
        in_class: bool = False,
        desc_metadata_factory: DescMetadataFactoryProtocol,
        ) -> ClassDesc:
    src_obj = cast(type, obj.obj_or_stub)
    config = obj.effective_config
    crossref = parent_crossref_namespace[name_in_parent]
    annotations = get_type_hints(
        src_obj, globalns=module_globals, include_extras=True)
    # Note that, especially in classes, it's extremely common to have
    # annotations that don't appear in the dict (eg dataclass fields).
    # But we don't want to clobber defined values, so we first extract
    # them here.
    bare_annotations = {
        name: Singleton.MISSING for name in annotations
        if name not in src_obj.__dict__}

    normalized_members: dict[str, NormalizedObj] = {}
    for name, value in itertools.chain(
        # Note that we don't want to do inspect.getmembers here, because
        # it will attempt to traverse the MRO, but we're messing with the
        # MRO as part of the stubbing process
        src_obj.__dict__.items(),
        bare_annotations.items()
    ):
        normalized_members[name] = normalize_namespace_item(
            name, value, annotations, config)

    namespace = {**parent_crossref_namespace}
    members: dict[
            str,
            ClassDesc | VariableDesc | CallableDesc | CrossrefDesc
        ] = {}
    for name, normalized_obj in normalized_members.items():
        classification = ObjClassification.from_obj(
            normalized_obj.obj_or_stub)
        desc_class = classification.get_desc_class()
        if desc_class is not None and issubclass(
            desc_class,
            ClassDesc | VariableDesc | CallableDesc | CrossrefDesc
        ):
            factory = _desc_factories[desc_class]
            namespace[name] = crossref / GetattrTraversal(name)
            members[name] = factory(
                name,
                namespace,
                normalized_obj,
                classification,
                module_globals=module_globals,
                desc_metadata_factory=desc_metadata_factory,
                in_class=True)

    if has_crossreffed_base(src_obj):
        bases = src_obj._docnote_extract_base_classes
    else:
        # Zeroth is always the class itself, which we want to skip
        bases = src_obj.__mro__[1:]

    if has_crossreffed_metaclass(src_obj):
        metaclass = TypeSpec.from_typehint(
            src_obj._docnote_extract_metaclass)
    elif (runtime_metaclass := type(src_obj)) is not type:
        metaclass = TypeSpec.from_typehint(runtime_metaclass)
    else:
        metaclass = None

    metadata = desc_metadata_factory(
        classification=classification,
        desc_class=ModuleDesc,
        crossref=crossref,
        annotateds=tuple(
            LazyResolvingValue.from_annotated(annotated)
            for annotated in obj.annotateds),
        metadata=config.metadata or {})
    metadata.include_in_docs_as_configured = \
        obj.effective_config.include_in_docs
    metadata.crossref_namespace = namespace
    metadata.canonical_module = (
        obj.canonical_module if obj.canonical_module is not Singleton.UNKNOWN
        else None)

    return ClassDesc(
        # Note: might differ from src_obj.__name__
        name=name_in_parent,
        crossref=crossref,
        ordering_index=obj.effective_config.ordering_index,
        child_groups=config.child_groups or (),
        parent_group_name=config.parent_group_name,
        metadata=metadata,
        metaclass=metaclass,
        bases=tuple(TypeSpec.from_typehint(base) for base in bases),
        members=frozenset(members.values()),
        docstring=extract_docstring(src_obj, config),)


@_desc_factory(CallableDesc)
def create_callable_desc(
        name_in_parent: str,
        parent_crossref_namespace: dict[str, Crossref],
        obj: NormalizedObj,
        classification: ObjClassification,
        *,
        in_class: bool = False,
        module_globals: dict[str, Any],
        desc_metadata_factory: DescMetadataFactoryProtocol,
        ) -> CallableDesc:
    """Given an object and its classification, construct a
    description instance, populating it with any required children.
    """
    crossref = parent_crossref_namespace[name_in_parent]
    src_obj = obj.obj_or_stub
    canonical_module = (
        obj.canonical_module
        if obj.canonical_module is not Singleton.UNKNOWN
        else None)
    # This MUST happen before unwrapping staticmethods and classmethods,
    # otherwise we end up back at the original function
    method_type = MethodType.classify(src_obj, in_class)

    # Staticmethods and classmethods are wrapped into descriptors that
    # aren't callables. We need to unwrap them first to be able to get
    # their signatures.
    if isinstance(src_obj, (staticmethod, classmethod)):
        src_obj = src_obj.__func__

    implementation_config = obj.effective_config
    # Note that this doesn't include the implementation, only the
    # overloads, so we still need to merge it with the signature from
    # inspecting the implementation
    try:
        overloads = get_overloads(src_obj)
    except AttributeError:
        logger.debug(
            'Failed to check overloads for %s. This is usually because it was '
            + 'a stlib object with a __module__ attribute, ex '
            + '``Decimal.__repr__``; however, this might indicate a bug.',
            src_obj)
        overloads = []

    namespace_expansion: dict[str, Crossref] = {}

    signatures: list[SignatureDesc] = []
    if overloads:
        for overload_ in overloads:
            overload_config_params: DocnoteConfigParams = {
                **implementation_config.get_stackables()}

            # This gets any config that was attrached via decorator.
            # TODO: we need a more general-purpose way of getting this
            # out, instead of spreading it between here and normalization
            if hasattr(overload_, DOCNOTE_CONFIG_ATTR):
                overload_config_params.update(
                    getattr(overload_, DOCNOTE_CONFIG_ATTR)
                    .as_nontotal_dict())

            overload_config = DocnoteConfig(**overload_config_params)
            # Note: we don't want to use this directly, because it would
            # incorrectly overlap with the no-overload traversal, and
            # because it would be redundant with all other un-indexed
            # overloads.
            if overload_config.ordering_index is None:
                signature_crossref = None
                namespace_expansion_key = ''
            else:
                # Note that this is required to make the signature, so
                # we can't wait until we know if a signature was actually
                # created; we have to just pop it afterwards if not.
                signature_crossref = crossref / SignatureTraversal(
                    overload_config.ordering_index)
                # Doing this here instead of after the signature is created
                # keeps the branch count lower
                namespace_expansion_key = \
                    f'__signature_{overload_config.ordering_index}__'
                namespace_expansion[namespace_expansion_key] = \
                    signature_crossref

            signature = _make_signature(
                parent_crossref_namespace,
                overload_,
                canonical_module,
                signature_crossref,
                signature_config=overload_config,
                parent_effective_config=obj.effective_config,
                module_globals=module_globals,
                desc_metadata_factory=desc_metadata_factory)
            if signature is None:
                namespace_expansion.pop(namespace_expansion_key, None)
            else:
                signatures.append(signature)

    # ``else`` is correct! If it defines overloads, then we want to rely ONLY
    # upon the overloads for the signature, and treat the implementation as
    # irrelevant for documentation purposes.
    else:
        signature_crossref = crossref / SignatureTraversal(None)
        signature = _make_signature(
            parent_crossref_namespace,
            src_obj,
            canonical_module,
            signature_crossref,
            signature_config=implementation_config,
            parent_effective_config=obj.effective_config,
            module_globals=module_globals,
            desc_metadata_factory=desc_metadata_factory)
        if signature is not None:
            signatures.append(signature)
            namespace_expansion['__signature_impl__'] = signature_crossref

    crossref = parent_crossref_namespace[name_in_parent]
    metadata = desc_metadata_factory(
        classification=classification,
        desc_class=ModuleDesc,
        crossref=crossref,
        annotateds=tuple(
            LazyResolvingValue.from_annotated(annotated)
            for annotated in obj.annotateds),
        metadata=obj.effective_config.metadata or {})
    metadata.include_in_docs_as_configured = \
        obj.effective_config.include_in_docs
    metadata.crossref_namespace = {
        **parent_crossref_namespace, **namespace_expansion}
    metadata.canonical_module = canonical_module

    return CallableDesc(
        # Note: might differ from src_obj.__name__
        name=name_in_parent,
        crossref=crossref,
        ordering_index=obj.effective_config.ordering_index,
        child_groups=obj.effective_config.child_groups or (),
        parent_group_name=obj.effective_config.parent_group_name,
        metadata=metadata,
        # Note that this is always the implementation docstring.
        docstring=extract_docstring(src_obj, implementation_config),
        color=CallableColor.ASYNC if classification.is_async
            else CallableColor.SYNC,
        method_type=method_type,
        is_generator=classification.is_any_generator,
        signatures=frozenset(signatures))


def _make_signature(  # noqa: PLR0913
        parent_crossref_namespace: dict[str, Crossref],
        src_obj: Callable,
        canonical_module: str | None,
        signature_crossref: Crossref | None,
        signature_config: DocnoteConfig,
        parent_effective_config: DocnoteConfig,
        *,
        module_globals: dict[str, Any],
        desc_metadata_factory: DescMetadataFactoryProtocol,
        ) -> SignatureDesc | None:
    """Extracts all the parameter-specific infos you need to create a
    signature object (including the retval), combining both the actual
    callable's signature and any type hints defined on the callable.

    TODO: this needs to add support for the object filters from the
    parent!
    """
    params: list[ParamDesc] = []
    try:
        annotations = get_type_hints(
            src_obj, globalns=module_globals, include_extras=True)
    except TypeError:
        logger.debug(
            'Failed to get type hints for %s for signature analysis. This is '
            + 'usually because the object is a from a stdlib/builtin callable '
            + 'or a C extension, but it might indicate a bug.', src_obj)
        annotations = {}

    try:
        raw_sig = inspect.Signature.from_callable(src_obj)
    except ValueError:
        logger.debug(
            'Failed to extract signature from %s. This is usually because the '
            + 'object is a from a stdlib/builtin callable or a C extension, '
            + 'but it might indicate a bug.', src_obj)
        return None

    # Note: we use the same namespace for all params in the signature,
    # and for the signature itself. Literally the same object, not
    # copies thereof. This ensures that all of the params are added,
    # so that params can reference each other.
    signature_namespace: dict[str, Crossref] = {
        **parent_crossref_namespace}

    for param_index, (param_name, raw_param) in enumerate(
        raw_sig.parameters.items()
    ):
        # Note: there's no escaping this. If we don't have a way to reference
        # the parent signature, we also don't have a way to reference sibling
        # parameters. It doesn't matter that they're relative to each other;
        # the underlying architecture assumes all crossrefs must work globally,
        # so there's no such thing as a relative crossref. (also, that would
        # make the implementation waaaaay more complicated)
        if signature_crossref is None:
            param_crossref = None
        else:
            param_crossref = signature_crossref / ParamTraversal(param_name)
            signature_namespace[param_name] = param_crossref

        style = ParamStyle.from_inspect_param_kind(raw_param.kind)
        if raw_param.default is inspect.Parameter.empty:
            default = None
        else:
            default = LazyResolvingValue.from_annotated(
                raw_param.default)

        annotation = annotations.get(param_name, Singleton.MISSING)
        normalized_annotation = normalize_annotation(annotation)
        combined_params: DocnoteConfigParams = {
            **parent_effective_config.get_stackables(),
            **normalized_annotation.config_params}
        effective_config = DocnoteConfig(**combined_params)

        param_metadata = desc_metadata_factory(
            classification=None,
            desc_class=ParamDesc,
            crossref=param_crossref,
            annotateds=normalized_annotation.annotateds,
            metadata=effective_config.metadata or {})
        param_metadata.include_in_docs_as_configured = \
            effective_config.include_in_docs
        param_metadata.crossref_namespace = signature_namespace
        param_metadata.canonical_module = canonical_module

        params.append(ParamDesc(
            name=param_name,
            index=param_index,
            crossref=param_crossref,
            ordering_index=effective_config.ordering_index,
            child_groups=effective_config.child_groups or (),
            parent_group_name=effective_config.parent_group_name,
            notes=textify_notes(
                normalized_annotation.notes, effective_config),
            style=style,
            default=default,
            typespec=normalized_annotation.typespec,
            metadata=param_metadata))

    if signature_crossref is None:
        retval_crossref = None
    else:
        retval_crossref = signature_crossref / ParamTraversal('return')
        signature_namespace['return'] = retval_crossref
    retval_annotation = annotations.get('return', Singleton.MISSING)
    normalized_retval_annotation = normalize_annotation(retval_annotation)
    combined_params: DocnoteConfigParams = {
        **parent_effective_config.get_stackables(),
        **normalized_retval_annotation.config_params}
    retval_effective_config = DocnoteConfig(**combined_params)

    retval_metadata = desc_metadata_factory(
        classification=None,
        desc_class=RetvalDesc,
        crossref=retval_crossref,
        annotateds=normalized_retval_annotation.annotateds,
        metadata=retval_effective_config.metadata or {})
    retval_metadata.include_in_docs_as_configured = \
        retval_effective_config.include_in_docs
    retval_metadata.crossref_namespace = signature_namespace
    retval_metadata.canonical_module = canonical_module

    signature_metadata = desc_metadata_factory(
        classification=None,
        desc_class=SignatureDesc,
        crossref=signature_crossref,
        annotateds=(),
        metadata=signature_config.metadata or {})
    signature_metadata.include_in_docs_as_configured = \
        signature_config.include_in_docs
    signature_metadata.crossref_namespace = signature_namespace
    signature_metadata.canonical_module = canonical_module
    return SignatureDesc(
        params=frozenset(params),
        retval=RetvalDesc(
            typespec=normalized_retval_annotation.typespec,
            notes=textify_notes(
                normalized_retval_annotation.notes, retval_effective_config),
            crossref=retval_crossref,
            ordering_index=retval_effective_config.ordering_index,
            child_groups=retval_effective_config.child_groups or (),
            parent_group_name=retval_effective_config.parent_group_name,
            metadata=retval_metadata
        ),
        docstring=None,
        crossref=signature_crossref,
        ordering_index=None,
        child_groups=signature_config.child_groups or (),
        parent_group_name=signature_config.parent_group_name,
        metadata=signature_metadata)


def _prepare_attr_namespace(
        parent_crossref: Crossref,
        parent_crossref_namespace: dict[str, Crossref] | None,
        attr_names: Iterable[str],
        ) -> dict[str, Crossref]:
    """This takes a sequence of child attribute names and constructs
    crossrefs for each of them. It then adds them to a namespace based
    only upon their name within the parent.
    """
    retval = {}

    if parent_crossref_namespace is not None:
        retval.update(parent_crossref_namespace)

    # Note: we're not doing any filtering here. That comes later. We really
    # just want to construct a namespace for all of the items.
    for attr_name in attr_names:
        retval[attr_name] = parent_crossref / GetattrTraversal(attr_name)

    return retval
