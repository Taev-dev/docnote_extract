from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated
from typing import Any
from typing import ClassVar
from typing import Protocol
from typing import TypeGuard
from typing import overload

from docnote import Note


@dataclass(slots=True)
class GetattrTraversal:
    name: str


@dataclass(slots=True)
class CallTraversal:
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


@dataclass(slots=True)
class GetitemTraversal:
    key: Any


@dataclass(slots=True, frozen=True)
class RefMetadata:
    """This class gets used to keep track of reference metadata.
    """
    module: str
    name: str
    traversals: Annotated[
            tuple[GetattrTraversal | CallTraversal | GetitemTraversal, ...],
            Note('''The traversal stack describes which extra steps were taken
                (attribute or getitem references, or function calls) to arrive
                at a final annotation. Empty tuples are used for plain toplevel
                module objects.
                ''')
        ] = ()


class Reftyped(Protocol):
    _docnote_extract_metadata: RefMetadata


class ClassWithReftypedBase(Protocol):
    _docnote_extract_base_classes: tuple[type]


class ClassWithReftypedMetaclass(Protocol):
    _docnote_extract_metaclass: RefMetadata


def is_reftyped(obj: Any) -> TypeGuard[Reftyped]:
    return hasattr(obj, '_docnote_extract_metadata')


def has_reftyped_base(obj: type) -> TypeGuard[ClassWithReftypedBase]:
    return hasattr(obj, '_docnote_extract_base_classes')


def has_reftyped_metaclass(obj: type) -> TypeGuard[ClassWithReftypedMetaclass]:
    return hasattr(obj, '_docnote_extract_metaclass')


class ReftypeMetaclass(type):
    """By necessity, the reftype objects need to be actual types, and
    not instances -- otherwise, you can't subclass them. Therefore, we
    need to support __getattr__, __getitem__, etc on the class itself;
    this is responsible for that.
    """
    _docnote_extract_metadata: RefMetadata

    def __new__(
            metacls,
            name: str,
            bases: tuple[type],
            namespace: dict[str, Any],
            *,
            __docnote_extract_traversal__: bool = False,
            # Kwargs here are needed in case something is subclassing from a
            # class with a defined metaclass, which itself accepts keywords
            **kwargs):
        """The goal here is to minimize the spread of the reftype
        metaclass, limiting it strictly to stubbed imports, and NOT
        objects actually defined in a module being inspected. We control
        this via the __docnote_extract_traversal__ magic keyword.
        """
        # The point here is that we can discard the metaclass for anything that
        # inherits from a ReftypeMixin. By requiring the unique keyword, which
        # only we supply (inside make_reftype), any other class instantiations
        # get a normal object.
        if __docnote_extract_traversal__:
            return super().__new__(metacls, name, bases, namespace)
        else:
            # We need to strip out our custom base class to avoid it injecting
            # the metaclass indirectly, causing infinite recursion.
            # The easiest way to do this is just drop it entirely, and not try
            # to replace it with something.
            stripped_bases = tuple(
                base for base in bases if not issubclass(base, ReftypeMixin))
            cls = super().__new__(type, name, stripped_bases, namespace)
            cls._docnote_extract_base_classes = bases
            return cls

    def __delattr__(cls, name: str) -> None: ...
    def __setattr__(cls, name: str, value: Any) -> None: ...
    def __getattr__(cls, name: str) -> type[ReftypeMixin]:
        return make_reftype(
            metadata=cls._docnote_extract_metadata,
            traversal=GetattrTraversal(name))

    def __delitem__(cls, key: Any) -> None: ...
    def __setitem__(cls, key: Any, value: Any) -> None: ...
    def __getitem__(cls, key: Any) -> type[ReftypeMixin]:
        return make_reftype(
            metadata=cls._docnote_extract_metadata,
            traversal=GetitemTraversal(key))


class ReftypeMixin(
        metaclass=ReftypeMetaclass,
        # Note: this is necessary for the metaclass to actually be applied,
        # otherwise it'll be stripped from the bases tuple and be replaced
        # with a normal type instance
        __docnote_extract_traversal__=True):
    """This is used as a mixin class when constructing Reftypes. It
    contains the actual implementation for the magic methods that return
    more reftypes.
    """
    _docnote_extract_metadata: ClassVar[RefMetadata]

    def __init_subclass__(cls, **kwargs):
        """We use this to suppress issues with our magic
        __docnote_extract_traversal__ parameter.
        """
        pass

    def __new__(cls, *args, **kwargs) -> type[ReftypeMixin]:
        """We use __new__ as a stand-in for a function call. Therefore,
        it creates a new concrete Reftype class, and returns it.
        """
        return make_reftype(
            metadata=cls._docnote_extract_metadata,
            traversal=CallTraversal(args, kwargs))


class ReftypeMetaclassMetaclass(type):
    """This "I'm-seeing-double"-ly-named class gets used as the base
    type for ``make_metaclass_reftype``. It does some magic to handle
    metaclass kwargs and strip out all traces of itself, while adding
    in the bookkeeping attribute to the final class.
    """

    def __new__(
            metacls,
            name: str,
            bases: tuple[type],
            namespace: dict[str, Any],
            # This is a stand-in for any kwargs from the stubbed-out metaclass.
            **kwargs):
        """In addition to handling any kwargs from the stubbed-out
        metaclass, this is responsible for reworking the bookkeeping a
        bit, replacing some weird metaclass shenanigans with an
        attribute on the final resulting class. Additionally, we remove
        ourselves from the metaclass hierarchy entirely -- so nach dem
        Motto "be kind, rewind".
        """
        injected_bases = (_SwallowsInitSubclassKwargs, *bases)

        if not is_reftyped(metacls):
            raise TypeError(
                'docnote_extract internal error: concrete MetaclassMetaclass '
                + 'is not reftyped!', metacls)

        metaclass_metadata = metacls._docnote_extract_metadata
        cls = super().__new__(type, name, injected_bases, namespace)
        cls._docnote_extract_metaclass = metaclass_metadata
        return cls


class _SwallowsInitSubclassKwargs:
    """We inject this as a base class for anything using the
    ReftypeMetaclassMetaclass so that subclass kwargs can be handled
    without error.
    """

    def __init_subclass__(cls, **kwargs): ...


def make_metaclass_reftype(
        *,
        module: str,
        name: str,
        ) -> type:
    """Metaclass reftypes don't implement any special logic beyond
    normal types. Therefore, they don't support mock-like behavior, nor
    traversals. However, unlike normal ``Reftype``s, they can -- as the
    name suggests -- be used as a metaclass.

    They also, of course, include the ``_docnote_extract_metadata``
    attribute on the created metaclass.
    """
    metadata = RefMetadata(module=module, name=name, traversals=())
    return type(
        'ReftypeMetaclassMetaclass',
        (ReftypeMetaclassMetaclass,),
        # We'll strip this out in just a second, but we need it to assign the
        # metadata for the _docnote_extract_metaclass attribute on the final
        # class object
        {'_docnote_extract_metadata': metadata})


@overload
def make_reftype(*, module: str, name: str) -> type[ReftypeMixin]: ...
@overload
def make_reftype(
        *,
        metadata: RefMetadata,
        traversal: GetattrTraversal | CallTraversal | GetitemTraversal
        ) -> type[ReftypeMixin]: ...
def make_reftype(
        *,
        module: str | None = None,
        name: str | None = None,
        metadata: RefMetadata | None = None,
        traversal:
            GetattrTraversal | CallTraversal | GetitemTraversal | None = None,
        ) -> type[ReftypeMixin]:
    """This makes an actual Reftype class.
    """
    if module is not None and name is not None:
        new_metadata = RefMetadata(module=module, name=name)

    elif metadata is not None and traversal is not None:
        new_metadata = RefMetadata(
            module=metadata.module,
            name=metadata.name,
            traversals=(*metadata.traversals, traversal))

    else:
        raise TypeError(
            'Invalid make_reftype call signature! (type checker failure?)')

    # This is separate purely so we can isolate the type: ignore
    retval = ReftypeMetaclass(
        'Reftype',
        (ReftypeMixin,),
        {'_docnote_extract_metadata': new_metadata},
        __docnote_extract_traversal__=True)
    return retval  # type: ignore
