from __future__ import annotations

import importlib

from docnote import DocnoteConfig

from docnote_extract.discovery import ModuleTreeNode
from docnote_extract.discovery import eager_import_submodules

from docnote_extract_testutils.fixtures import purge_cached_testpkg_modules


class TestEagerImportSubmodules:

    @purge_cached_testpkg_modules
    def test_handrolled(self):
        """The handrolled test submodule, which itself includes
        submodules, must return the expected results.
        """
        root_module = importlib.import_module(
            'docnote_extract_testpkg._hand_rolled')
        retval = {}
        eager_import_submodules(root_module, loaded_modules=retval)
        print(set(retval))
        assert set(retval) == {
            'docnote_extract_testpkg._hand_rolled.child1',
            'docnote_extract_testpkg._hand_rolled.child1._private',
            'docnote_extract_testpkg._hand_rolled.child2',
            'docnote_extract_testpkg._hand_rolled.child2.nested_child',
            'docnote_extract_testpkg._hand_rolled.child2.some_sibling',
            'docnote_extract_testpkg._hand_rolled.imports_3p_metaclass',
            'docnote_extract_testpkg._hand_rolled.imports_from_parent',
            'docnote_extract_testpkg._hand_rolled.subclasses_3p_class'}


class TestModuleTreeNode:

    def test_find(self):
        """Finding the child of a root node must, yknow, return the
        child.
        """
        tree = ModuleTreeNode(
            'foo',
            'foo',
            {'bar': ModuleTreeNode(
                'foo.bar',
                'bar',
                {'baz': ModuleTreeNode(
                    'foo.bar.baz',
                    'baz',
                    effective_config=DocnoteConfig())},
                effective_config=DocnoteConfig())},
            effective_config=DocnoteConfig())
        assert tree.find('foo.bar.baz').fullname == 'foo.bar.baz'
