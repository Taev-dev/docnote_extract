from docnote_extract._crossrefs import CallTraversal
from docnote_extract._crossrefs import Crossref
from docnote_extract._crossrefs import CrossrefMetaclass
from docnote_extract._crossrefs import CrossrefMixin
from docnote_extract._crossrefs import GetattrTraversal
from docnote_extract._crossrefs import GetitemTraversal
from docnote_extract._crossrefs import has_crossreffed_base
from docnote_extract._crossrefs import has_crossreffed_metaclass
from docnote_extract._crossrefs import is_crossreffed
from docnote_extract._crossrefs import make_crossreffed
from docnote_extract._crossrefs import make_metaclass_crossreffed


class TestMakeMetaclassCrossref:

    def test_creation_succeeds(self):
        """Calling the function must succeed and return a type
        subclass with the correct attribute set.
        """
        retval = make_metaclass_crossreffed(module='foo', name='Bar')
        assert issubclass(retval, type)
        assert is_crossreffed(retval)
        assert retval._docnote_extract_metadata.module_name == 'foo'
        assert retval._docnote_extract_metadata.toplevel_name == 'Bar'
        assert not retval._docnote_extract_metadata.traversals

    def test_metaclass_usage_succeeds(self):
        """The result of a metaclass reftype must be usable as a
        metaclass.
        """
        retval = make_metaclass_crossreffed(module='foo', name='Bar')

        class TestClass(metaclass=retval, foo='oof'):  # type: ignore
            ...

        assert not is_crossreffed(type(TestClass))
        assert not is_crossreffed(TestClass)
        assert has_crossreffed_metaclass(TestClass)
        assert type(TestClass) is type


class TestMakeCrossref:

    def test_from_module(self):
        """When called with a module and member name, the returned value
        must be a reftype class as expected.
        """
        retval = make_crossreffed(module='foo', name='bar')
        assert is_crossreffed(retval)
        assert isinstance(retval, type)
        assert issubclass(retval, CrossrefMixin)
        assert retval._docnote_extract_metadata.module_name == 'foo'
        assert retval._docnote_extract_metadata.toplevel_name == 'bar'
        assert not retval._docnote_extract_metadata.traversals

    def test_from_traversal(self):
        """When called with an existing metadata and a traversal, the
        returned value must be a reftype class as expected.
        """
        src_metadata = Crossref(
            module_name='foo',
            toplevel_name='bar',
            traversals=(GetattrTraversal('baz'),))
        retval = make_crossreffed(
            metadata=src_metadata,
            traversal=GetattrTraversal('zab'))
        assert is_crossreffed(retval)
        assert isinstance(retval, type)
        assert issubclass(retval, CrossrefMixin)
        assert retval._docnote_extract_metadata.module_name == 'foo'
        assert retval._docnote_extract_metadata.toplevel_name == 'bar'
        assert retval._docnote_extract_metadata.traversals == (
            GetattrTraversal('baz'), GetattrTraversal('zab'))

    def test_subclass_usage_succeeds(self):
        """Usage of a normal reftype as a parent class must succeed.
        """
        retval = make_crossreffed(module='foo', name='Bar')

        # Note: parent classes might change their metaclass and accept kwargs!
        class TestClass(retval, foo='oof'):  # type: ignore
            ...

        assert not is_crossreffed(type(TestClass))
        assert not is_crossreffed(TestClass)
        assert has_crossreffed_base(TestClass)
        assert type(TestClass) is type


class TestCrossrefMetaclass:

    def test_traversal_eq_true_gets_meta(self):
        """Classes that are explicitly annotated with our magic
        __docnote_extract_traversal__=True must have the metaclass
        applied.
        """
        class TestClass(
                CrossrefMixin,
                # Implied by the mixin, but explicit for type checking purposes
                metaclass=CrossrefMetaclass,
                __docnote_extract_traversal__=True):
            _docnote_extract_metadata = Crossref(
                module_name='foo', toplevel_name='bar')

        assert is_crossreffed(TestClass)
        assert isinstance(TestClass, type)
        assert issubclass(TestClass, CrossrefMixin)
        assert type(TestClass) is CrossrefMetaclass

    def test_traversal_eq_false_skips_meta(self):
        """Classes not explicitly annotated with our magic
        __docnote_extract_traversal__=True must not have the metaclass
        applied.
        """
        class TestClass(
                CrossrefMixin,
                # Implied by the mixin, but explicit for type checking purposes
                metaclass=CrossrefMetaclass):
            _docnote_extract_metadata = Crossref(
                module_name='foo', toplevel_name='bar')

        assert is_crossreffed(TestClass)
        assert isinstance(TestClass, type)
        assert not issubclass(TestClass, CrossrefMixin)
        assert type(TestClass) is not CrossrefMetaclass


class TestCrossrefMixin:

    def test_getattr_traversal(self):
        """Doing a getattr on the CrossrefMixin class must return a new
        reftype instance with a subsequent getattr traversal.
        """
        class TestClass(CrossrefMixin, __docnote_extract_traversal__=True):
            _docnote_extract_metadata = Crossref(
                module_name='foo', toplevel_name='bar')

        retval = TestClass.baz
        assert is_crossreffed(retval)
        assert isinstance(retval, type)
        assert issubclass(retval, CrossrefMixin)
        assert retval._docnote_extract_metadata.module_name == 'foo'
        assert retval._docnote_extract_metadata.toplevel_name == 'bar'
        assert retval._docnote_extract_metadata.traversals == (
            GetattrTraversal('baz'),)

    def test_getitem_traversal(self):
        """Doing a getitem on the CrossrefMixin class must return a new
        reftype instance with a subsequent getitem traversal.
        """
        class TestClass(CrossrefMixin, __docnote_extract_traversal__=True):
            _docnote_extract_metadata = Crossref(
                module_name='foo', toplevel_name='bar')

        retval = TestClass[42]
        assert is_crossreffed(retval)
        assert isinstance(retval, type)
        assert issubclass(retval, CrossrefMixin)
        assert retval._docnote_extract_metadata.module_name == 'foo'
        assert retval._docnote_extract_metadata.toplevel_name == 'bar'
        assert retval._docnote_extract_metadata.traversals == (
            GetitemTraversal(42),)

    def test_call_traversal(self):
        """Doing a call on the CrossrefMixin class must return a new
        reftype instance with a subsequent call traversal.
        """
        class TestClass(CrossrefMixin, __docnote_extract_traversal__=True):
            _docnote_extract_metadata = Crossref(
                module_name='foo', toplevel_name='bar')

        retval = TestClass('foo', 'bar', baz='zab')
        assert is_crossreffed(retval)
        assert isinstance(retval, type)
        assert issubclass(retval, CrossrefMixin)
        assert retval._docnote_extract_metadata.module_name == 'foo'
        assert retval._docnote_extract_metadata.toplevel_name == 'bar'
        assert retval._docnote_extract_metadata.traversals == (
            CallTraversal(args=('foo', 'bar'), kwargs={'baz': 'zab'}),)
