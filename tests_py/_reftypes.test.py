from docnote_extract._reftypes import CallTraversal
from docnote_extract._reftypes import GetattrTraversal
from docnote_extract._reftypes import GetitemTraversal
from docnote_extract._reftypes import RefMetadata
from docnote_extract._reftypes import ReftypeMetaclass
from docnote_extract._reftypes import ReftypeMixin
from docnote_extract._reftypes import has_reftyped_base
from docnote_extract._reftypes import has_reftyped_metaclass
from docnote_extract._reftypes import is_reftyped
from docnote_extract._reftypes import make_metaclass_reftype
from docnote_extract._reftypes import make_reftype


class TestMakeMetaclassReftype:

    def test_creation_succeeds(self):
        """Calling the function must succeed and return a type
        subclass with the correct attribute set.
        """
        retval = make_metaclass_reftype(module='foo', name='Bar')
        assert issubclass(retval, type)
        assert is_reftyped(retval)
        assert retval._docnote_extract_metadata.module == 'foo'
        assert retval._docnote_extract_metadata.name == 'Bar'
        assert not retval._docnote_extract_metadata.traversals

    def test_metaclass_usage_succeeds(self):
        """The result of a metaclass reftype must be usable as a
        metaclass.
        """
        retval = make_metaclass_reftype(module='foo', name='Bar')

        class TestClass(metaclass=retval, foo='oof'):  # type: ignore
            ...

        assert not is_reftyped(type(TestClass))
        assert not is_reftyped(TestClass)
        assert has_reftyped_metaclass(TestClass)
        assert type(TestClass) is type


class TestMakeReftype:

    def test_from_module(self):
        """When called with a module and member name, the returned value
        must be a reftype class as expected.
        """
        retval = make_reftype(module='foo', name='bar')
        assert is_reftyped(retval)
        assert isinstance(retval, type)
        assert issubclass(retval, ReftypeMixin)
        assert retval._docnote_extract_metadata.module == 'foo'
        assert retval._docnote_extract_metadata.name == 'bar'
        assert not retval._docnote_extract_metadata.traversals

    def test_from_traversal(self):
        """When called with an existing metadata and a traversal, the
        returned value must be a reftype class as expected.
        """
        src_metadata = RefMetadata(
            module='foo', name='bar', traversals=(GetattrTraversal('baz'),))
        retval = make_reftype(
            metadata=src_metadata,
            traversal=GetattrTraversal('zab'))
        assert is_reftyped(retval)
        assert isinstance(retval, type)
        assert issubclass(retval, ReftypeMixin)
        assert retval._docnote_extract_metadata.module == 'foo'
        assert retval._docnote_extract_metadata.name == 'bar'
        assert retval._docnote_extract_metadata.traversals == (
            GetattrTraversal('baz'), GetattrTraversal('zab'))

    def test_subclass_usage_succeeds(self):
        """Usage of a normal reftype as a parent class must succeed.
        """
        retval = make_reftype(module='foo', name='Bar')

        # Note: parent classes might change their metaclass and accept kwargs!
        class TestClass(retval, foo='oof'):  # type: ignore
            ...

        assert not is_reftyped(type(TestClass))
        assert not is_reftyped(TestClass)
        assert has_reftyped_base(TestClass)
        assert type(TestClass) is type


class TestReftypeMetaclass:

    def test_traversal_eq_true_gets_meta(self):
        """Classes that are explicitly annotated with our magic
        __docnote_extract_traversal__=True must have the metaclass
        applied.
        """
        class TestClass(
                ReftypeMixin,
                # Implied by the mixin, but explicit for type checking purposes
                metaclass=ReftypeMetaclass,
                __docnote_extract_traversal__=True):
            _docnote_extract_metadata = RefMetadata(module='foo', name='bar')

        assert is_reftyped(TestClass)
        assert isinstance(TestClass, type)
        assert issubclass(TestClass, ReftypeMixin)
        assert type(TestClass) is ReftypeMetaclass

    def test_traversal_eq_false_skips_meta(self):
        """Classes not explicitly annotated with our magic
        __docnote_extract_traversal__=True must not have the metaclass
        applied.
        """
        class TestClass(
                ReftypeMixin,
                # Implied by the mixin, but explicit for type checking purposes
                metaclass=ReftypeMetaclass):
            _docnote_extract_metadata = RefMetadata(module='foo', name='bar')

        assert is_reftyped(TestClass)
        assert isinstance(TestClass, type)
        assert not issubclass(TestClass, ReftypeMixin)
        assert type(TestClass) is not ReftypeMetaclass


class TestReftypeMixin:

    def test_getattr_traversal(self):
        """Doing a getattr on the ReftypeMixin class must return a new
        reftype instance with a subsequent getattr traversal.
        """
        class TestClass(ReftypeMixin, __docnote_extract_traversal__=True):
            _docnote_extract_metadata = RefMetadata(module='foo', name='bar')

        retval = TestClass.baz
        assert is_reftyped(retval)
        assert isinstance(retval, type)
        assert issubclass(retval, ReftypeMixin)
        assert retval._docnote_extract_metadata.module == 'foo'
        assert retval._docnote_extract_metadata.name == 'bar'
        assert retval._docnote_extract_metadata.traversals == (
            GetattrTraversal('baz'),)

    def test_getitem_traversal(self):
        """Doing a getitem on the ReftypeMixin class must return a new
        reftype instance with a subsequent getitem traversal.
        """
        class TestClass(ReftypeMixin, __docnote_extract_traversal__=True):
            _docnote_extract_metadata = RefMetadata(module='foo', name='bar')

        retval = TestClass[42]
        assert is_reftyped(retval)
        assert isinstance(retval, type)
        assert issubclass(retval, ReftypeMixin)
        assert retval._docnote_extract_metadata.module == 'foo'
        assert retval._docnote_extract_metadata.name == 'bar'
        assert retval._docnote_extract_metadata.traversals == (
            GetitemTraversal(42),)

    def test_call_traversal(self):
        """Doing a call on the ReftypeMixin class must return a new
        reftype instance with a subsequent call traversal.
        """
        class TestClass(ReftypeMixin, __docnote_extract_traversal__=True):
            _docnote_extract_metadata = RefMetadata(module='foo', name='bar')

        retval = TestClass('foo', 'bar', baz='zab')
        assert is_reftyped(retval)
        assert isinstance(retval, type)
        assert issubclass(retval, ReftypeMixin)
        assert retval._docnote_extract_metadata.module == 'foo'
        assert retval._docnote_extract_metadata.name == 'bar'
        assert retval._docnote_extract_metadata.traversals == (
            CallTraversal(args=('foo', 'bar'), kwargs={'baz': 'zab'}),)
