from __future__ import annotations

import importlib
from unittest.mock import patch

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
        assert set(retval) == {
            'docnote_extract_testpkg._hand_rolled.child1',
            'docnote_extract_testpkg._hand_rolled.child1._private',
            'docnote_extract_testpkg._hand_rolled.child2',
            'docnote_extract_testpkg._hand_rolled.child2.nested_child',
            'docnote_extract_testpkg._hand_rolled.child2.some_sibling',
            'docnote_extract_testpkg._hand_rolled.imports_3p_metaclass',
            'docnote_extract_testpkg._hand_rolled.imports_from_parent',
            'docnote_extract_testpkg._hand_rolled.subclasses_3p_class',
            'docnote_extract_testpkg._hand_rolled.noteworthy',
            'docnote_extract_testpkg._hand_rolled.relativity',
            'docnote_extract_testpkg._hand_rolled.uses_import_names',}

    @purge_cached_testpkg_modules
    def test_no_extra_import_attempts(self):
        """When iterating over the handrolled test module,
        eager_import_submodules must only attempt to import modules
        from within the test module -- none outside of it -- and must
        also correctly skip already-imported modules.
        """
        root_module = importlib.import_module(
            'docnote_extract_testpkg._hand_rolled')
        retval = {}

        with patch(
            'docnote_extract.discovery.import_module',
            autospec=True,
            wraps=importlib.import_module
        ) as import_module_wrapper:
            eager_import_submodules(root_module, loaded_modules=retval)

        import_requests = [
            call.args[0] for call in import_module_wrapper.call_args_list]
        unique_import_requests = set(import_requests)

        assert len(import_requests) == len(unique_import_requests)
        assert unique_import_requests == {
            'docnote_extract_testpkg._hand_rolled.child1',
            'docnote_extract_testpkg._hand_rolled.child1._private',
            'docnote_extract_testpkg._hand_rolled.child2',
            'docnote_extract_testpkg._hand_rolled.child2.nested_child',
            'docnote_extract_testpkg._hand_rolled.child2.some_sibling',
            'docnote_extract_testpkg._hand_rolled.imports_3p_metaclass',
            'docnote_extract_testpkg._hand_rolled.imports_from_parent',
            'docnote_extract_testpkg._hand_rolled.subclasses_3p_class',
            'docnote_extract_testpkg._hand_rolled.noteworthy',
            'docnote_extract_testpkg._hand_rolled.relativity',
            'docnote_extract_testpkg._hand_rolled.uses_import_names',}
