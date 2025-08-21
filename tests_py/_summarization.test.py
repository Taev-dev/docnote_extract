from __future__ import annotations

from docnote_extract._summarization import _prepare_attr_namespace
from docnote_extract.crossrefs import Crossref
from docnote_extract.crossrefs import GetattrTraversal


class TestPrepareAttrNamespace:

    def test_with_parent_namespace(self):
        """When called with a parent namespace, it must merge it and
        the children together.
        """
        parent_crossref = Crossref(module_name='foo', toplevel_name='Foo')
        parent_namespace = {'Foo': parent_crossref}
        attrs = ['bar', 'baz']

        retval = _prepare_attr_namespace(
            parent_crossref, parent_namespace, attrs)

        assert len(retval) == 3
        assert set(retval) == {'Foo', 'bar', 'baz'}
        assert retval['bar'] == parent_crossref / GetattrTraversal('bar')

    def test_without_parent_namespace(self):
        """When called without a parent namespace, it succeed.
        """
        parent_crossref = Crossref(module_name='foo', toplevel_name='Foo')
        attrs = ['bar', 'baz']

        retval = _prepare_attr_namespace(parent_crossref, None, attrs)

        assert len(retval) == 2
        assert set(retval) == {'bar', 'baz'}
        assert retval['bar'] == parent_crossref / GetattrTraversal('bar')
