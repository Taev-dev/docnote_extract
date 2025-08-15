from __future__ import annotations

import inspect
import typing
from collections.abc import Sequence
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Annotated
from typing import Any
from typing import Protocol

from docnote import DocnoteGroup
from docnote import MarkupLang
from docnote import Note

from docnote_extract._crossrefs import Crossref
from docnote_extract._crossrefs import CrossrefTraversal
from docnote_extract._crossrefs import GetattrTraversal
from docnote_extract._crossrefs import ParamTraversal
from docnote_extract._crossrefs import SignatureTraversal
from docnote_extract._crossrefs import is_crossreffed

if typing.TYPE_CHECKING:
    from docnote_extract.normalization import LazyResolvingValue
    from docnote_extract.normalization import TypeSpec


class Singleton(Enum):
    MISSING = 'missing'
    UNKNOWN = 'unknown'


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

    def get_desc_class(self) -> type[DescBase] | None:
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


class DescMetadataProtocol(Protocol):
    include_in_docs_as_configured: Annotated[
        bool | None,
        Note('''This directly copies the underlying object's
            ``DocnoteConfig.included_in_docts`` value, and represents an
            explicit override by the code author.

            It is set after the metadata instance is created via the
            factory method passed to ``summarize_module``, and then used
            to help determine the final value of ``include_in_docs``
            during final filtering.''')]
    include_in_docs_final: Annotated[
        bool,
        Note('''This value is set during final filtering, and reflects
            whether or not the value is ^^directly^ included in the
            final docs (note that it might still be ^^indirectly^^
            included -- for example as an aside -- but that this is
            dependent upon the documentation generator).

            Documentation generators can use this to, for example,
            implicitly include any mixin methods of a private base class
            in the documentation of its public descendants.
            ''')]
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
            namespace of the surrounding module.

            This value is set after the metadata instance is created via the
            factory method passed to ``summarize_module``. It is not used by
            ``docref_extract``; it purely exists for documentation generators.
            ''')]


class DescMetadataFactoryProtocol[T: DescMetadataProtocol](Protocol):

    def __call__(
            self,
            *,
            classification: ObjClassification | None,
            desc_class: type[DescBase],
            crossref: Crossref | None,
            annotateds: Annotated[
                tuple[LazyResolvingValue, ...],
                Note('''``Annotated`` instances (other than docnote ones)
                    declared on the object will be included here.

                    Note that any imported annotation will take the form of a
                    ``LazyResolvingValue``. These must be called to resolve
                    the actuall annotation.

                    This part of the API should be considered experimental and
                    subject to change.''')],
            metadata: Annotated[
                dict[str, Any],
                Note(
                    'Any metadata defined via ``DocnoteConfig`` attachments.'
                )],
            ) -> T:
        """A description metadata factory function must be passed to
        ``summarize_module`` to create the individual metadata instances
        to include in the description objects.
        """
        ...


class _DescBaseProtocol[T: DescMetadataProtocol](Protocol):

    def traverse(self, traversal: CrossrefTraversal) -> DescBase[T]:
        """If the object has a traversal with the passed name, return
        it. Otherwise, raise ``LookupError``.
        """
        ...


@dataclass(slots=True, frozen=True, kw_only=True)
class DescBase[T: DescMetadataProtocol](_DescBaseProtocol[T]):
    crossref: Crossref | None
    ordering_index: int | None
    child_groups: Annotated[
            Sequence[DocnoteGroup],
            Note('Any child groups defined via ``DocnoteConfig`` attachments.')
        ]
    parent_group_name: Annotated[
            str | None,
            Note(''''Any parent group assignment defined via ``DocnoteConfig``
                attachments.''')]
    metadata: T = field(compare=False, repr=False)

    def __truediv__(self, traversal: CrossrefTraversal) -> DescBase[T]:
        return self.traverse(traversal)


@dataclass(slots=True, frozen=True, kw_only=True)
class ModuleDesc[T: DescMetadataProtocol](DescBase[T]):
    name: Annotated[str, Note('The module fullname, ex ``foo.bar.baz``.')]
    dunder_all: frozenset[str]
    docstring: DocText | None
    members: frozenset[
        ClassDesc[T]
        | VariableDesc[T]
        | CallableDesc[T]
        | CrossrefDesc[T]]

    _member_lookup: dict[
            CrossrefTraversal,
            ClassDesc[T] | VariableDesc[T] | CallableDesc[T] | CrossrefDesc[T]
        ] = field(default_factory=dict, repr=False, init=False, compare=False)

    def __post_init__(self):
        for member in self.members:
            self._member_lookup[GetattrTraversal(member.name)] = member

    def traverse(self, traversal: CrossrefTraversal) -> DescBase[T]:
        # KeyError is a LookupError subclass, so this is fine.
        return self._member_lookup[traversal]


@dataclass(slots=True, frozen=True, kw_only=True)
class CrossrefDesc[T: DescMetadataProtocol](DescBase[T]):
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

    def traverse(self, traversal: CrossrefTraversal) -> DescBase[T]:
        raise LookupError(
            'Crossref descriptions have no traversals', self, traversal)


@dataclass(slots=True, frozen=True, kw_only=True)
class VariableDesc[T: DescMetadataProtocol](DescBase[T]):
    """VariableDesc instances are used for module variables as well as
    class members. Note that within a class, variables annotated as
    ``ClassVar``s will have the literal ``ClassVar`` added to their
    ``annotations`` tuple.

    TODO: classvar, Final, etc
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

    def traverse(self, traversal: CrossrefTraversal) -> DescBase[T]:
        raise LookupError(
            'Variable descriptions have no traversals', self, traversal)


@dataclass(slots=True, frozen=True, kw_only=True)
class ClassDesc[T: DescMetadataProtocol](DescBase[T]):
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
    members: frozenset[
        ClassDesc[T]
        | VariableDesc[T]
        | CallableDesc[T]
        | CrossrefDesc[T]]

    _member_lookup: dict[
            CrossrefTraversal,
            ClassDesc[T] | VariableDesc[T] | CallableDesc[T] | CrossrefDesc[T]
        ] = field(default_factory=dict, repr=False, init=False, compare=False)

    def __post_init__(self):
        for member in self.members:
            self._member_lookup[GetattrTraversal(member.name)] = member

    def traverse(self, traversal: CrossrefTraversal) -> DescBase[T]:
        # KeyError is a LookupError subclass, so this is fine.
        return self._member_lookup[traversal]


@dataclass(slots=True, frozen=True, kw_only=True)
class CallableDesc[T: DescMetadataProtocol](DescBase[T]):
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
    signatures: frozenset[SignatureDesc[T]]

    _member_lookup: dict[SignatureTraversal, SignatureDesc[T]] = field(
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

    def traverse(self, traversal: CrossrefTraversal) -> DescBase[T]:
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


@dataclass(slots=True, frozen=True, kw_only=True)
class SignatureDesc[T: DescMetadataProtocol](DescBase[T]):
    """These are used to express a particular combination of parameters
    and return values. Callables with a single signature will typically
    have only one of these (with the exception of union types that have
    separate ``Note``s attached to individual members of the union).
    Overloaded callables will have one ``SignatureSpec`` per overload.
    """
    params: frozenset[ParamDesc[T]]
    retval: RetvalDesc[T]
    docstring: Annotated[
            DocText | None,
            Note('''In practice, this is typically None. However, it will be
                non-None if:
                ++  The parent callable defines overloads
                ++  The overloads themselves have docstrings
                Note that in this case, the docstring for the implementation
                will be included in the parent callable.''')]

    _member_lookup: dict[ParamTraversal, ParamDesc[T]] = field(
        default_factory=dict, repr=False, init=False, compare=False)

    def __post_init__(self):
        for member in self.params:
            self._member_lookup[ParamTraversal(member.name)] = member

    def traverse(self, traversal: CrossrefTraversal) -> DescBase[T]:
        if not isinstance(traversal, ParamTraversal):
            raise LookupError(
                'Traversals for signatures must be ``ParamTraversal`` '
                + 'instances!', self, traversal)

        if traversal.name == 'return':
            return self.retval

        # KeyError is a LookupError subclass, so this is fine.
        return self._member_lookup[traversal]


@dataclass(slots=True, frozen=True, kw_only=True)
class ParamDesc[T: DescMetadataProtocol](DescBase[T]):
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

    def traverse(self, traversal: CrossrefTraversal) -> DescBase[T]:
        raise LookupError(
            'Param descriptions have no traversals', self, traversal)


@dataclass(slots=True, frozen=True, kw_only=True)
class RetvalDesc[T: DescMetadataProtocol](DescBase[T]):
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

    def traverse(self, traversal: CrossrefTraversal) -> DescBase[T]:
        raise LookupError(
            'Retval descriptions have no traversals', self, traversal)
