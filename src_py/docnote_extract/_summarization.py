from __future__ import annotations

import inspect
import itertools
from collections.abc import Callable
from collections.abc import Sequence
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Annotated
from typing import Any
from typing import Protocol
from typing import Self
from typing import cast
from typing import get_overloads
from typing import get_type_hints

from docnote import DOCNOTE_CONFIG_ATTR
from docnote import DocnoteConfig
from docnote import DocnoteConfigParams
from docnote import DocnoteGroup
from docnote import MarkupLang
from docnote import Note

from docnote_extract._crossrefs import Crossref
from docnote_extract._crossrefs import CrossrefTraversal
from docnote_extract._crossrefs import GetattrTraversal
from docnote_extract._crossrefs import ParamTraversal
from docnote_extract._crossrefs import SignatureTraversal
from docnote_extract._crossrefs import has_crossreffed_base
from docnote_extract._crossrefs import has_crossreffed_metaclass
from docnote_extract._crossrefs import is_crossreffed
from docnote_extract._extraction import ModulePostExtraction
from docnote_extract._types import Singleton
from docnote_extract.discovery import ModuleTreeNode
from docnote_extract.discovery import validate_config
from docnote_extract.filtering import ModuleObjectFilter
from docnote_extract.filtering import ObjectFilter
from docnote_extract.filtering import filter_inclusion_rules
from docnote_extract.filtering import filter_module_members
from docnote_extract.normalization import LazyResolvingValue
from docnote_extract.normalization import NormalizedObj
from docnote_extract.normalization import TypeSpec
from docnote_extract.normalization import normalize_annotation
from docnote_extract.normalization import normalize_namespace_item


def summarize_module(
        module: ModulePostExtraction,
        normalized_objs: Annotated[
                dict[str, NormalizedObj],
                Note('All module members, with no filters applied.')],
        module_tree: ModuleTreeNode,
        module_object_filters: Annotated[
                Sequence[ModuleObjectFilter],
                Note('''Filters to apply to the direct descendants of the
                    module itself -- ie, the toplevel items in normalized_objs.
                    ''')
            ] = (filter_module_members,),
        object_filters: Annotated[
                Sequence[ObjectFilter],
                Note('''Filters to apply to the module members' internals --
                    for example, to filter out private members of a class.
                    ''')
            ] = (filter_inclusion_rules,)
        ) -> ModuleDesc:
    """For the passed post-extraction module, iterates across all
    normalized_objs and extracts their descriptions, returning them
    combined into a single ``ModuleDesc``.
    """
    module_crossref = Crossref(
        module_name=module.__name__,
        toplevel_name=None)
    namespace = _prepare_namespace(module_crossref, None, normalized_objs)

    filtered_objs = normalized_objs
    for module_obj_filter in module_object_filters:
        filtered_objs = module_obj_filter(module, filtered_objs)

    module_members = set()
    for name, normalized_obj in filtered_objs.items():
        classification = ObjClassification.from_obj(normalized_obj.obj_or_stub)
        desc_class = classification.get_desc_class()
        if desc_class is not None:
            module_members.add(desc_class.from_obj(
                name,
                namespace,
                normalized_obj,
                classification,
                object_filters,
                module_globals=module.__dict__))

    config = module_tree.find(module.__name__).effective_config
    desc = ModuleDesc(
        crossref=module_crossref,
        name=module.__name__,
        ordering_index=config.ordering_index,
        crossref_namespace=namespace,
        annotateds=(),
        parent_group_name=None,
        child_groups=config.child_groups or (),
        metadata=config.metadata or {},
        dunder_all=frozenset(getattr(module, '__all__', ())),
        docstring=_extract_docstring(module, config),
        members=frozenset(module_members))
    return desc


@dataclass(slots=True)
class ObjClassification:
    is_reftype: bool
    has_traversals: bool | None
    is_module: bool
    is_class: bool
    is_method: bool
    is_function: bool
    is_generator_function: bool
    is_generator: bool
    is_coroutine_function: bool
    is_coroutine: bool
    is_awaitable: bool
    is_async_generator_function: bool
    is_async_generator: bool
    is_method_wrapper: bool
    # Note: the primary place you're likely to encounter these in third-party
    # code is as the type of a slot. So for example, any dataclass with
    # slots=True will have this type on its attributes. As per stdlib docs,
    # these are **never** a function, class, method, or builtin.
    # ... but it's still True for int.__add__. Errrm??? Confusing AF.
    is_method_descriptor: bool
    is_data_descriptor: bool
    is_getset_descriptor: bool
    is_member_descriptor: bool
    is_callable: bool

    @property
    def is_any_generator(self) -> bool:
        return (
            self.is_generator_function
            or self.is_generator
            or self.is_async_generator_function
            or self.is_async_generator)

    @property
    def is_async(self) -> bool:
        return (
            self.is_coroutine_function
            or self.is_coroutine
            or self.is_awaitable
            or self.is_async_generator_function
            or self.is_async_generator)

    @classmethod
    def from_obj(cls, obj: Any) -> ObjClassification:
        if (crossreffed := is_crossreffed(obj)):
            has_traversals = bool(obj._docnote_extract_metadata.traversals)
        else:
            has_traversals = None

        return cls(
            is_reftype=crossreffed,
            has_traversals=has_traversals,
            is_module=inspect.ismodule(obj),
            is_class=inspect.isclass(obj),
            is_method=inspect.ismethod(obj),
            is_function=inspect.isfunction(obj),
            is_generator_function=inspect.isgeneratorfunction(obj),
            is_generator=inspect.isgenerator(obj),
            is_coroutine_function=inspect.iscoroutinefunction(obj),
            is_coroutine=inspect.iscoroutine(obj),
            is_awaitable=inspect.isawaitable(obj),
            is_async_generator_function=inspect.isasyncgenfunction(obj),
            is_async_generator=inspect.isasyncgen(obj),
            is_method_wrapper=inspect.ismethodwrapper(obj),
            is_method_descriptor=inspect.ismethoddescriptor(obj),
            is_data_descriptor=inspect.isdatadescriptor(obj),
            is_getset_descriptor=inspect.isgetsetdescriptor(obj),
            is_member_descriptor=inspect.ismemberdescriptor(obj),
            is_callable=callable(obj))

    def get_desc_class(self) -> type[_DescBase] | None:
        """Given the current classification, returns which description
        type should be applied to the object, so that the caller can
        then create a description instance for it.

        Returns None if no description should be created -- for example,
        if the object was a reftype.
        """
        if self.is_reftype:
            if self.has_traversals:
                return VariableDesc
            else:
                return CrossrefDesc
        if self.is_class:
            return ClassDesc
        if self.is_module:
            return ModuleDesc
        if (
            self.is_method
            or self.is_function
            or self.is_generator_function
            or self.is_coroutine_function
            or self.is_async_generator_function
            or self.is_method_wrapper
            or (self.is_member_descriptor and self.is_callable)
            or (self.is_method_descriptor and self.is_callable)
        ):
            return CallableDesc

        return VariableDesc


class CallableColor(Enum):
    ASYNC = 'async'
    SYNC = 'sync'


class MethodType(Enum):
    INSTANCE = 'instance'
    CLASS = 'class'
    STATIC = 'static'

    @staticmethod
    def classify(src_obj: Any, in_class: bool) -> MethodType | None:
        """Classifies a (hopefully callable) into a method type, or
        None if no method was applicable.

        Note that if you're in a class, you must BOTH set in_class
        to True, **and also get the ``src_obj`` from the class
        ``__dict__``, and ^^not by direct getattr reference on the
        class!^^**. Eg ``cls.__dict__['foo']``, **not** ``cls.foo``.
        The latter won't work!
        """
        if isinstance(src_obj, classmethod):
            return MethodType.CLASS
        elif isinstance(src_obj, staticmethod):
            return MethodType.STATIC
        elif in_class:
            return MethodType.INSTANCE

        return None


class ParamStyle(Enum):
    KW_ONLY = 'kw_only'
    KW_STARRED = 'kw_starred'
    POS_ONLY = 'pos_only'
    POS_STARRED = 'pos_starred'
    POS_OR_KW = 'pos_or_kw'

    @classmethod
    def from_inspect_param_kind(cls, kind) -> ParamStyle:
        if kind is inspect.Parameter.POSITIONAL_ONLY:
            return ParamStyle.POS_ONLY
        if kind is inspect.Parameter.POSITIONAL_OR_KEYWORD:
            return ParamStyle.POS_OR_KW
        if kind is inspect.Parameter.VAR_POSITIONAL:
            return ParamStyle.POS_STARRED
        if kind is inspect.Parameter.KEYWORD_ONLY:
            return ParamStyle.KW_ONLY
        if kind is inspect.Parameter.VAR_KEYWORD:
            return ParamStyle.KW_STARRED

        raise TypeError('Not a member of ``inspect.Parameter.kind``!', kind)


@dataclass(slots=True, frozen=True, kw_only=True)
class DocText:
    value: str
    markup_lang: str | MarkupLang | None


class _DescBaseProtocol(Protocol):

    @classmethod
    def from_obj(
            cls,
            name_in_parent: str,
            parent_crossref_namespace: dict[str, Crossref],
            obj: NormalizedObj,
            classification: ObjClassification,
            object_filters: Sequence[ObjectFilter],
            *,
            module_globals: dict[str, Any],
            in_class: bool = False,
            ) -> Self:
        """Given an object and its classification, construct a
        description instance, populating it with any required children.
        """
        ...

    def traverse(self, traversal: CrossrefTraversal) -> _DescBase:
        """If the object has a traversal with the passed name, return
        it. Otherwise, raise ``LookupError``.
        """
        ...


@dataclass(slots=True, frozen=True, kw_only=True)
class _DescBase(_DescBaseProtocol):
    crossref: Crossref | None
    ordering_index: int | None
    annotateds: Annotated[
        tuple[LazyResolvingValue, ...],
        Note('''``Annotated`` instances (other than docnote ones) declared on
            the object will be included here. Additional generics (eg
            ``ClassVar``, ``Final``, etc) will also be included.

            Note that any imported annotation will take the form of a
            ``LazyResolvingValue``. These must be called to resolve
            the actuall annotation, **after** first uninstalling the
            import hook.

            Inclusion of annotations should be considered an experimental
            feature; their API is likely to change in the future.''')]
    crossref_namespace: Annotated[
        dict[str, Crossref],
        Note('''This contains a snapshot of any objects contained within
            the locals and globals for the member that can be expressed as
            ``Crossref`` instances. Objects within ``locals`` and ``globals``
            that cannot be expressed as a ``Crossref`` will be omitted.

            The primary intended use of this is for automatic linking of
            code-fenced blocks -- for example, if you reference ``Foo`` in
            the docstring of ``Bar``, this could be used to automatically
            link back to ``Foo`` in post-processing.

            This can also be used when processing python code embedded within
            docstrings themselves, if -- for example -- you wanted to run
            doctests against the code block while automatically applying the
            namespace of the surrounding module.''')
        ] = field(compare=False, repr=False)
    child_groups: Annotated[
            Sequence[DocnoteGroup],
            Note('Any child groups defined via ``DocnoteConfig`` attachments.')
        ]
    parent_group_name: Annotated[
            str | None,
            Note(''''Any parent group assignment defined via ``DocnoteConfig``
                attachments.''')]
    metadata: Annotated[
            dict[str, Any],
            Note('Any metadata defined via ``DocnoteConfig`` attachments.')
        ] = field(compare=False)

    def __truediv__(self, traversal: CrossrefTraversal) -> _DescBase:
        return self.traverse(traversal)


@dataclass(slots=True, frozen=True, kw_only=True)
class ModuleDesc(_DescBase):
    name: Annotated[str, Note('The module fullname, ex ``foo.bar.baz``.')]
    dunder_all: frozenset[str]
    docstring: DocText | None
    members: frozenset[ClassDesc | VariableDesc | CallableDesc | CrossrefDesc]

    _member_lookup: dict[
            CrossrefTraversal,
            ClassDesc | VariableDesc | CallableDesc | CrossrefDesc
        ] = field(default_factory=dict, repr=False, init=False, compare=False)

    def __post_init__(self):
        for member in self.members:
            self._member_lookup[GetattrTraversal(member.name)] = member

    def traverse(self, traversal: CrossrefTraversal) -> _DescBase:
        # KeyError is a LookupError subclass, so this is fine.
        return self._member_lookup[traversal]

    @classmethod
    def from_obj(
            cls,
            name_in_parent: str,
            parent_crossref_namespace: dict[str, Crossref],
            obj: NormalizedObj,
            classification: ObjClassification,
            object_filters: Sequence[ObjectFilter],
            *,
            module_globals: dict[str, Any],
            in_class: bool = False,
            ) -> Self:
        """It sorta... violates our protocol... but modules are an
        exception to the rule when it comes to ``from_obj``; they just
        can't support it, because they don't have parents, aren't
        normalized objects, etc.
        """
        raise TypeError(
            'Module descriptions cannot be created directly from objects!')


@dataclass(slots=True, frozen=True, kw_only=True)
class CrossrefDesc(_DescBase):
    """Used when something is being re-exported (at the module level) or
    is otherwise a direct reference to something else (for example, a
    classvar referencing an imported enum value).
    """
    name: str
    typespec: Annotated[
        TypeSpec | None,
        Note('''Typically None. An explicit type annotation on the re-export,
            in addition to any annotation from its definition site.''')]
    notes: Annotated[
        tuple[DocText, ...],
        Note('''The contents of any ``Note``s directly attached to the
            re-export (in addition to any notes from its definition site).''')]
    src_crossref: Crossref

    def traverse(self, traversal: CrossrefTraversal) -> _DescBase:
        raise LookupError(
            'Re-export descriptions have no traversals', self, traversal)

    @classmethod
    def from_obj(
            cls,
            name_in_parent: str,
            parent_crossref_namespace: dict[str, Crossref],
            obj: NormalizedObj,
            classification: ObjClassification,
            object_filters: Sequence[ObjectFilter],
            *,
            module_globals: dict[str, Any],
            in_class: bool = False,
            ) -> Self:
        """Given an object and its classification, construct a
        description instance, populating it with any required children.
        """
        src_obj = obj.obj_or_stub
        # Note: this cannot have traversals, or it would have been classified
        # as a VariableDesc instead of a re-export.
        if not is_crossreffed(src_obj):
            raise TypeError(
                'Impossible branch: re-export from non-reftype!', obj)

        return cls(
            name=name_in_parent,
            src_crossref=src_obj._docnote_extract_metadata,
            typespec=obj.typespec,
            notes=_textify_notes(obj.notes, obj.effective_config),
            crossref=parent_crossref_namespace[name_in_parent],
            ordering_index=obj.effective_config.ordering_index,
            annotateds=tuple(
                LazyResolvingValue.from_annotated(annotated)
                for annotated in obj.annotateds),
            crossref_namespace=parent_crossref_namespace,
            child_groups=obj.effective_config.child_groups or (),
            parent_group_name=obj.effective_config.parent_group_name,
            metadata=obj.effective_config.metadata or {})


@dataclass(slots=True, frozen=True, kw_only=True)
class VariableDesc(_DescBase):
    """VariableDesc instances are used for module variables as well as
    class members. Note that within a class, variables annotated as
    ``ClassVar``s will have the literal ``ClassVar`` added to their
    ``annotations`` tuple.
    """
    name: str
    typespec: Annotated[
        TypeSpec | None,
        Note('''Note that a value of ``None`` indicates that no type hint was
            defined, not that the hint itself was an explicit ``None``. The
            latter case will be a ``Crossref`` with object source, ``None``
            as the module name, ane ``None`` as the name.''')]
    notes: Annotated[
        tuple[DocText, ...],
        Note('The contents of any ``Note``s attached to the variable.')]

    def traverse(self, traversal: CrossrefTraversal) -> _DescBase:
        raise LookupError(
            'Variable descriptions have no traversals', self, traversal)

    @classmethod
    def from_obj(
            cls,
            name_in_parent: str,
            parent_crossref_namespace: dict[str, Crossref],
            obj: NormalizedObj,
            classification: ObjClassification,
            object_filters: Sequence[ObjectFilter],
            *,
            module_globals: dict[str, Any],
            in_class: bool = False,
            ) -> Self:
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

        # if isinstance(src_obj, property):
            
        # If missing, use the runtime type as an inference -- unless the
        # object was a bare annotation (without a typespec?! weird), then
        # we can't do anything.
        if obj.typespec is None and src_obj is not Singleton.MISSING:
            typespec = TypeSpec.from_typehint(type(src_obj))
        else:
            typespec = obj.typespec

        return cls(
            name=name_in_parent,
            typespec=typespec,
            notes=_textify_notes(obj.notes, obj.effective_config),
            crossref=parent_crossref_namespace[name_in_parent],
            ordering_index=obj.effective_config.ordering_index,
            annotateds=tuple(
                LazyResolvingValue.from_annotated(annotated)
                for annotated in obj.annotateds),
            crossref_namespace=parent_crossref_namespace,
            child_groups=obj.effective_config.child_groups or (),
            parent_group_name=obj.effective_config.parent_group_name,
            metadata=obj.effective_config.metadata or {})


@dataclass(slots=True, frozen=True, kw_only=True)
class ClassDesc(_DescBase):
    """
    """
    name: str
    docstring: DocText | None
    metaclass: Annotated[
        TypeSpec | None,
        Note('''Note that this only includes an explicit metaclass, as defined
            on the class itself. Implicit metaclasses inherited from base
            classes will not be detected.''')]
    bases: tuple[TypeSpec, ...]
    members: frozenset[ClassDesc | VariableDesc | CallableDesc | CrossrefDesc]

    _member_lookup: dict[
            CrossrefTraversal,
            ClassDesc | VariableDesc | CallableDesc | CrossrefDesc
        ] = field(default_factory=dict, repr=False, init=False, compare=False)

    def __post_init__(self):
        for member in self.members:
            self._member_lookup[GetattrTraversal(member.name)] = member

    def traverse(self, traversal: CrossrefTraversal) -> _DescBase:
        # KeyError is a LookupError subclass, so this is fine.
        return self._member_lookup[traversal]

    @classmethod
    def from_obj(
            cls,
            name_in_parent: str,
            parent_crossref_namespace: dict[str, Crossref],
            obj: NormalizedObj,
            classification: ObjClassification,
            object_filters: Sequence[ObjectFilter],
            *,
            module_globals: dict[str, Any],
            in_class: bool = False,
            ) -> Self:
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
            src_obj.__dict__.items(),
            bare_annotations.items()
        ):
            normalized_members[name] = normalize_namespace_item(
                name, value, annotations, config)

        filtered_members = normalized_members
        for object_filter in object_filters:
            filtered_members = object_filter(filtered_members)

        namespace = {**parent_crossref_namespace}
        members: dict[
                str,
                ClassDesc | VariableDesc | CallableDesc | CrossrefDesc
            ] = {}
        for name, normalized_obj in filtered_members.items():
            classification = ObjClassification.from_obj(
                normalized_obj.obj_or_stub)
            desc_class = classification.get_desc_class()
            if desc_class is not None and issubclass(
                desc_class,
                ClassDesc | VariableDesc | CallableDesc | CrossrefDesc
            ):
                namespace[name] = crossref / GetattrTraversal(name)
                members[name] = desc_class.from_obj(
                    name,
                    namespace,
                    normalized_obj,
                    classification,
                    object_filters,
                    module_globals=module_globals,
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

        return cls(
            # Note: might differ from src_obj.__name__
            name=name_in_parent,
            crossref=crossref,
            ordering_index=obj.effective_config.ordering_index,
            annotateds=tuple(
                LazyResolvingValue.from_annotated(annotated)
                for annotated in obj.annotateds),
            crossref_namespace=namespace,
            child_groups=config.child_groups or (),
            parent_group_name=config.parent_group_name,
            metadata=config.metadata or {},
            metaclass=metaclass,
            bases=tuple(TypeSpec.from_typehint(base) for base in bases),
            members=frozenset(members.values()),
            docstring=_extract_docstring(src_obj, config),)


@dataclass(slots=True, frozen=True, kw_only=True)
class CallableDesc(_DescBase):
    """
    """
    name: str
    docstring: Annotated[
            DocText | None,
            Note('''For non-overloaded callables, this is simply the value
                of the callable's docstring.

                For overloaded callables, this is specifically the docstring
                associated with the callable **implementation**, and not its
                overloads.''')]
    color: CallableColor
    method_type: MethodType | None
    is_generator: bool
    signatures: frozenset[SignatureDesc]

    _member_lookup: dict[SignatureTraversal, SignatureDesc] = field(
        default_factory=dict, repr=False, init=False, compare=False)

    def __post_init__(self):
        # We can just skip the single-signature version entirely; we don't
        # need a lookup for it (see ``traverse``)
        if len(self.signatures) > 1:
            for member in self.signatures:
                if member.ordering_index is not None:
                    # Note: these aren't necessarily sequential, nor are they
                    # necessarily in order!
                    self._member_lookup[
                        SignatureTraversal(member.ordering_index)] = member

    @classmethod
    def from_obj(
            cls,
            name_in_parent: str,
            parent_crossref_namespace: dict[str, Crossref],
            obj: NormalizedObj,
            classification: ObjClassification,
            object_filters: Sequence[ObjectFilter],
            *,
            in_class: bool = False,
            module_globals: dict[str, Any],
            ) -> Self:
        """Given an object and its classification, construct a
        description instance, populating it with any required children.
        """
        crossref = parent_crossref_namespace[name_in_parent]
        src_obj = obj.obj_or_stub
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
        except Exception as exc:
            print('-----------------')
            print(f'{callable(src_obj)=}, {classification.is_callable=}')
            print(f'{name_in_parent=}, {src_obj=}')
            raise
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
                else:
                    signature_crossref = crossref / SignatureTraversal(
                        overload_config.ordering_index)
                    namespace_expansion[
                        f'__signature_{overload_config.ordering_index}__'
                    ] = signature_crossref
                params, retval_desc, signature_namespace = \
                    _make_signature_params(
                        parent_crossref_namespace,
                        src_obj,
                        signature_crossref,
                        obj.effective_config,
                        module_globals=module_globals)
                signatures.append(SignatureDesc(
                    params=params,
                    retval=retval_desc,
                    docstring=_extract_docstring(
                        overload_, overload_config),
                    crossref=signature_crossref,
                    ordering_index=overload_config.ordering_index,
                    crossref_namespace=signature_namespace,
                    annotateds=(),
                    child_groups=overload_config.child_groups or (),
                    parent_group_name=overload_config.parent_group_name,
                    metadata=overload_config.metadata or {}))

        else:
            signature_crossref = crossref / SignatureTraversal(None)
            params, retval_desc, signature_namespace = _make_signature_params(
                parent_crossref_namespace,
                src_obj,
                signature_crossref,
                obj.effective_config,
                module_globals=module_globals)
            signatures.append(SignatureDesc(
                params=params,
                retval=retval_desc,
                docstring=None,
                crossref=signature_crossref,
                ordering_index=None,
                crossref_namespace=signature_namespace,
                annotateds=(),
                child_groups=implementation_config.child_groups or (),
                parent_group_name=implementation_config.parent_group_name,
                metadata=implementation_config.metadata or {}))
            namespace_expansion['__signature_impl__'] = signature_crossref

        return cls(
            # Note: might differ from src_obj.__name__
            name=name_in_parent,
            crossref=parent_crossref_namespace[name_in_parent],
            ordering_index=obj.effective_config.ordering_index,
            annotateds=tuple(
                LazyResolvingValue.from_annotated(annotated)
                for annotated in obj.annotateds),
            crossref_namespace={
                **parent_crossref_namespace, **namespace_expansion},
            child_groups=obj.effective_config.child_groups or (),
            parent_group_name=obj.effective_config.parent_group_name,
            metadata=obj.effective_config.metadata or {},
            # Note that this is always the implementation docstring.
            docstring=_extract_docstring(src_obj, implementation_config),
            color=CallableColor.ASYNC if classification.is_async
                else CallableColor.SYNC,
            method_type=method_type,
            is_generator=classification.is_any_generator,
            signatures=frozenset(signatures))

    def traverse(self, traversal: CrossrefTraversal) -> _DescBase:
        """Traversals into callables work like this:
        ++  A callable with a single signature (ie, with no overloads)
            is always referenced by ``ordering_index=None``
        ++  A callable with multiple signatures (ie, with overloads,
            or with unions where each union member has separate
            ``Note``s attached) can only be referenced by the explicit
            ``ordering_index`` attached to it by a ``DocnoteConfig``.
            If none is defined (ie, if default ordering is used), it
            cannot be referenced by traversal.
        """
        if not isinstance(traversal, SignatureTraversal):
            raise LookupError('Invalid traversal type!', self, traversal)

        # There's no reason for a lookup here, we can just validate the
        # traversal and return the only possible result
        if len(self.signatures) == 1:
            if traversal.ordering_index is not None:
                raise LookupError(
                    '``ordering_index`` for non-overloaded callables must '
                    + ' always be None', self, traversal)
            return next(iter(self.signatures))

        if traversal not in self._member_lookup:
            raise LookupError(
                'Traversals for overloaded callables must match the explicit '
                + "``ordering_index`` defined on the signature's attached "
                + '``DocnoteConfig', self, traversal)

        return self._member_lookup[traversal]


def _make_signature_params(
        parent_crossref_namespace: dict[str, Crossref],
        src_obj: Callable,
        signature_crossref: Crossref | None,
        parent_effective_config: DocnoteConfig,
        *,
        module_globals: dict[str, Any]
        ) -> tuple[frozenset[ParamDesc], RetvalDesc, dict[str, Crossref]]:
    """Extracts all the parameter-specific infos you need to create a
    signature object (including the retval), combining both the actual
    callable's signature and any type hints defined on the callable.

    TODO: this needs to add support for the object filters from the
    parent!
    """
    params: list[ParamDesc] = []
    annotations = get_type_hints(
        src_obj, globalns=module_globals, include_extras=True)
    raw_sig = inspect.Signature.from_callable(src_obj)
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

        params.append(ParamDesc(
            name=param_name,
            index=param_index,
            crossref=param_crossref,
            ordering_index=effective_config.ordering_index,
            crossref_namespace=signature_namespace,
            annotateds=normalized_annotation.annotateds,
            child_groups=effective_config.child_groups or (),
            parent_group_name=effective_config.parent_group_name,
            notes=_textify_notes(
                normalized_annotation.notes, effective_config),
            style=style,
            default=default,
            typespec=normalized_annotation.typespec,
            metadata=effective_config.metadata or {}))

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

    return frozenset(params), RetvalDesc(
        typespec=normalized_retval_annotation.typespec,
        notes=_textify_notes(
            normalized_retval_annotation.notes, retval_effective_config),
        crossref=retval_crossref,
        ordering_index=retval_effective_config.ordering_index,
        crossref_namespace=signature_namespace,
        annotateds=normalized_retval_annotation.annotateds,
        child_groups=retval_effective_config.child_groups or (),
        parent_group_name=retval_effective_config.parent_group_name,
        metadata=retval_effective_config.metadata or {}
    ), signature_namespace


@dataclass(slots=True, frozen=True, kw_only=True)
class SignatureDesc(_DescBase):
    """These are used to express a particular combination of parameters
    and return values. Callables with a single signature will typically
    have only one of these (with the exception of union types that have
    separate ``Note``s attached to individual members of the union).
    Overloaded callables will have one ``SignatureSpec`` per overload.
    """
    params: frozenset[ParamDesc]
    retval: RetvalDesc
    docstring: Annotated[
            DocText | None,
            Note('''In practice, this is typically None. However, it will be
                non-None if:
                ++  The parent callable defines overloads
                ++  The overloads themselves have docstrings
                Note that in this case, the docstring for the implementation
                will be included in the parent callable.''')]

    _member_lookup: dict[ParamTraversal, ParamDesc] = field(
        default_factory=dict, repr=False, init=False, compare=False)

    def __post_init__(self):
        for member in self.params:
            self._member_lookup[ParamTraversal(member.name)] = member

    def traverse(self, traversal: CrossrefTraversal) -> _DescBase:
        if not isinstance(traversal, ParamTraversal):
            raise LookupError(
                'Traversals for signatures must be ``ParamTraversal`` '
                + 'instances!', self, traversal)

        if traversal.name == 'return':
            return self.retval

        # KeyError is a LookupError subclass, so this is fine.
        return self._member_lookup[traversal]

    @classmethod
    def from_obj(
            cls,
            name_in_parent: str,
            parent_crossref_namespace: dict[str, Crossref],
            obj: NormalizedObj,
            classification: ObjClassification,
            object_filters: Sequence[ObjectFilter],
            *,
            module_globals: dict[str, Any],
            in_class: bool = False,
            ) -> Self:
        """It sorta... violates our protocol... but signatures are an
        exception to the rule when it comes to ``from_obj``; they must
        be explicitly created by a CallableDesc.
        """
        raise TypeError(
            'Signature descriptions cannot be created directly from objects!')


@dataclass(slots=True, frozen=True, kw_only=True)
class ParamDesc(_DescBase):
    """
    """
    name: str
    index: int
    style: ParamStyle
    default: LazyResolvingValue | None
    typespec: Annotated[
        TypeSpec | None,
        Note('''Note that a value of ``None`` indicates that no type hint was
            defined, not that the hint itself was an explicit ``None``. The
            latter case will be a ``Crossref`` with object source, ``None``
            as the module name, ane ``None`` as the name.''')]
    notes: Annotated[
        tuple[DocText, ...],
        Note('The contents of any ``Note``s attached to the param.')]

    def traverse(self, traversal: CrossrefTraversal) -> _DescBase:
        raise LookupError(
            'Param descriptions have no traversals', self, traversal)

    @classmethod
    def from_obj(
            cls,
            name_in_parent: str,
            parent_crossref_namespace: dict[str, Crossref],
            obj: NormalizedObj,
            classification: ObjClassification,
            object_filters: Sequence[ObjectFilter],
            *,
            module_globals: dict[str, Any],
            in_class: bool = False,
            ) -> Self:
        """It sorta... violates our protocol... but param descs are an
        exception to the rule when it comes to ``from_obj``; they must
        be explicitly created by a CallableDesc.
        """
        raise TypeError(
            'Param descriptions cannot be created directly from objects!')


@dataclass(slots=True, frozen=True, kw_only=True)
class RetvalDesc(_DescBase):
    """
    """
    typespec: Annotated[
        TypeSpec | None,
        Note('''Note that a value of ``None`` indicates that no type hint was
            defined, not that the hint itself was an explicit ``None``. The
            latter case will be a ``Crossref`` with object source, ``None``
            as the module name, ane ``None`` as the name.''')]
    notes: Annotated[
        tuple[DocText, ...],
        Note('The contents of any ``Note``s attached to the return value.')]

    def traverse(self, traversal: CrossrefTraversal) -> _DescBase:
        raise LookupError(
            'Retval descriptions have no traversals', self, traversal)

    @classmethod
    def from_obj(
            cls,
            name_in_parent: str,
            parent_crossref_namespace: dict[str, Crossref],
            obj: NormalizedObj,
            classification: ObjClassification,
            object_filters: Sequence[ObjectFilter],
            *,
            module_globals: dict[str, Any],
            in_class: bool = False,
            ) -> Self:
        """It sorta... violates our protocol... but retval descs are an
        exception to the rule when it comes to ``from_obj``; they must
        be explicitly created by a CallableDesc.
        """
        raise TypeError(
            'Retval descriptions cannot be created directly from objects!')


def _extract_docstring(
        obj: Any,
        effective_config: DocnoteConfig
        ) -> DocText | None:
    """Gets the DocText version of the docstring, if one is defined.
    Otherwise, returns None.
    """
    # Note that this gets cleaned up internally by ``inspect.cleandoc`` (see
    # stdlib docs) and also normalized to str | None.
    raw_clean_docstring = inspect.getdoc(obj)
    if not raw_clean_docstring or raw_clean_docstring.isspace():
        return None
    else:
        return DocText(
            value=raw_clean_docstring,
            markup_lang=effective_config.markup_lang)


def _prepare_namespace(
        parent_crossref: Crossref,
        parent_crossref_namespace: dict[str, Crossref] | None,
        # Note that this needs to be ALL normalized objects, **not** just the
        # ones that have been filtered to "belong" to the parent!
        normalized_objs: dict[str, NormalizedObj],
        ) -> dict[str, Crossref]:
    """This takes the normalized objects for a particular scope and
    converts them into a namespace, as used in the description objects.
    """
    retval = {}
    parent_is_module = parent_crossref.toplevel_name is None

    if parent_crossref_namespace is not None:
        retval.update(parent_crossref_namespace)

    for name, normalized_obj in normalized_objs.items():
        if parent_is_module:
            # Unknowns must be discarded here, because we won't be able to
            # construct a reference to them.
            # Nones are nonsensical, since they're only used in situations
            # where the parent is not a module.
            # Therefore, limit to strings.
            if (
                isinstance(normalized_obj.canonical_module, str)
                and isinstance(normalized_obj.canonical_name, str)
            ):
                # Note that the canonical name might not match the retval[name]
                # (because it could have been renamed in the parent namespace)
                retval[name] = Crossref(
                    module_name=normalized_obj.canonical_module,
                    toplevel_name=normalized_obj.canonical_name)

        else:
            retval[name] = parent_crossref / GetattrTraversal(name)

    return retval


def _textify_notes(
        raw_notes: Sequence[Note],
        effective_config: DocnoteConfig
        ) -> tuple[DocText, ...]:
    retval: list[DocText] = []
    for raw_note in raw_notes:
        # Note that the passed effective_config will already have been
        # validated at this point, but not the note's direct config.
        if raw_note.config is not None:
            # Note that we don't want just the stackables here; this is already
            # an effective config for the thing the note is attached to, so
            # we've already applied stacking rules. We want the whole thing.
            combination: DocnoteConfigParams = {
                **effective_config.as_nontotal_dict(),
                **raw_note.config.as_nontotal_dict()}
            effective_config = DocnoteConfig(**combination)
            validate_config(effective_config, f'On-note config for {raw_note}')

        retval.append(DocText(
            value=inspect.cleandoc(raw_note.value),
            markup_lang=effective_config.markup_lang))

    return tuple(retval)
