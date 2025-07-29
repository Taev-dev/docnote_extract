from importlib import import_module
from typing import cast

from docnote_extract._extraction import ModulePostExtraction
from docnote_extract._types import Singleton
from docnote_extract.normalization import NormalizedObj
from docnote_extract.normalization import normalize_module_dict

from docnote_extract_testutils.fixtures import purge_cached_testpkg_modules


class TestNormalizeModuleMembers:
    """Performs spot tests against a testpkg module that does no
    stubbing and has no dependencies (so that we can isolate stubbing
    behavior from the normalization step).

    Note that integration tests are responsible for checking modules
    that DO perform stubbing, both with and without stub bypasses.
    """
    @purge_cached_testpkg_modules
    def test_return_type_correct(self):
        """All returned objects must be _NormaliezdObj instances. The
        entire module dict must be returned in the normalized output.
        """
        docnote = cast(
            ModulePostExtraction,
            import_module('docnote_extract_testpkg.taevcode.docnote'))
        docnote._docnote_extract_import_tracking_registry = {}

        normalized = normalize_module_dict(docnote)

        assert all(
            isinstance(obj, NormalizedObj) for obj in normalized.values())
        assert set(normalized) == set(docnote.__dict__)

    @purge_cached_testpkg_modules
    def test_local_class(self):
        """A class defined within the current module must be assigned
        the correct canonical origin.
        """
        docnote = cast(
            ModulePostExtraction,
            import_module('docnote_extract_testpkg.taevcode.docnote'))
        docnote._docnote_extract_import_tracking_registry = {}

        normalized = normalize_module_dict(docnote)

        norm_note = normalized['Note']
        assert not norm_note.annotations
        assert norm_note.type_ is Singleton.MISSING
        assert norm_note.canonical_module == \
            'docnote_extract_testpkg.taevcode.docnote'
        assert norm_note.canonical_name == 'Note'
