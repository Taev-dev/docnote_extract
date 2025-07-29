import importlib
import sys
from unittest.mock import patch

import pytest

from docnote_extract._extraction import ReftypeMarker
from docnote_extract._extraction import _ExtractionFinderLoader
from docnote_extract._extraction import _ExtractionPhase
from docnote_extract._extraction import mark_special_reftype
from docnote_extract._reftypes import RefMetadata
from docnote_extract._reftypes import has_reftyped_base
from docnote_extract._reftypes import has_reftyped_metaclass
from docnote_extract._reftypes import is_reftyped

import docnote_extract_testpkg
import docnote_extract_testpkg._hand_rolled
import docnote_extract_testutils
from docnote_extract_testutils.fixtures import purge_cached_testpkg_modules
from docnote_extract_testutils.fixtures import set_inspection
from docnote_extract_testutils.fixtures import set_phase


def fake_discover_factory(module_names: list[str]):
    """This creates a factory that returns ``discover_all_modules``
    fakes. We need this extra step because the logic in
    ``discover_and_extract`` relies upon ``discover_all_modules``
    actually importing the modules.
    """
    def fake_discover_all_modules(*args, **kwargs):
        for module_name in module_names:
            importlib.import_module(module_name)

        return module_names

    return fake_discover_all_modules


class TestExtractionFinderLoader:

    @set_inspection('')
    @set_phase(_ExtractionPhase.EXTRACTION)
    @purge_cached_testpkg_modules
    def test_uninstall_also_removes_imported_modules(self):
        """Uninstalling the import hook must also remove any stubbed
        modules from sys.modules.
        """
        floader = _ExtractionFinderLoader(
            frozenset({'docnote_extract_testpkg'}),
            module_stash_nostub_raw={
                'docnote_extract_testpkg': docnote_extract_testpkg})
        assert 'docnote_extract_testpkg' not in sys.modules

        floader.install()
        try:
            importlib.import_module('docnote_extract_testpkg')
            assert 'docnote_extract_testpkg' in sys.modules
        finally:
            floader.uninstall()

        assert 'docnote_extract_testpkg' not in sys.modules

    @set_inspection('')
    @set_phase(_ExtractionPhase.EXTRACTION)
    @purge_cached_testpkg_modules
    def test_stubbs_returned_after_installation(self):
        """To ensure park security, imports after installation must be
        escorted by at least one host. Errr, wait, got caught in a
        reverie, wrong thing. After installing the import hook,
        importing a not-under-inspection module must return a stubbed
        module. After uninstallation, the normal module must be
        returned.
        """
        # Empty here just because we want to test stuff against testpkg
        floader = _ExtractionFinderLoader(frozenset())

        floader.install()
        try:
            floader._stash_prehook_modules()
            try:
                testpkg = importlib.import_module('docnote_extract_testutils')
                assert 'docnote_extract_testutils' in sys.modules
                assert is_reftyped(testpkg)
            finally:
                floader._unstash_prehook_modules()
        finally:
            floader.uninstall()

        assert 'docnote_extract_testutils' not in sys.modules
        assert testpkg is not docnote_extract_testutils
        testpkg_reloaded = importlib.import_module('docnote_extract_testutils')
        assert testpkg_reloaded is not testpkg
        assert not is_reftyped(testpkg_reloaded)

    @set_phase(_ExtractionPhase.EXTRACTION)
    @set_inspection('docnote_extract_testpkg._hand_rolled')
    @purge_cached_testpkg_modules
    def test_inspection_leaves_target_unstubbed(self):
        """After installing the import hook and while inspecting a
        module, the returned module (and later imports thereof) must
        return the module being inspected itself, and not a stubbed
        version thereof.
        """
        assert 'pytest' in sys.modules

        floader = _ExtractionFinderLoader(
            frozenset({'docnote_extract_testpkg'}),
            nostub_packages=frozenset({'pytest'}),
            module_stash_nostub_raw={
                'docnote_extract_testpkg': docnote_extract_testpkg,
                'docnote_extract_testpkg._hand_rolled':
                    docnote_extract_testpkg._hand_rolled})

        floader.install()
        try:
            floader._stash_prehook_modules()
            try:
                testpkg = importlib.import_module(
                    'docnote_extract_testpkg._hand_rolled')
                assert testpkg is not docnote_extract_testpkg._hand_rolled
                assert 'docnote_extract_testpkg._hand_rolled' in sys.modules
                assert not is_reftyped(testpkg)
                assert testpkg.SOME_CONSTANT == 7
            finally:
                floader._unstash_prehook_modules()
        finally:
            floader.uninstall()

        assert 'docnote_extract_testpkg._hand_rolled' not in sys.modules
        assert 'docnote_extract_testpkg' not in sys.modules
        assert 'pytest' in sys.modules

    @patch('docnote_extract._extraction.discover_all_modules', autospec=True)
    @purge_cached_testpkg_modules
    def test_inspection_works_with_metaclasses(self, mock_discover):
        """After installing the import hook and while inspecting a
        module, modules that create classes using imported third-party
        metaclasses must still be inspectable.
        """
        # Mock this out so we don't check literally the entire testpkg
        mock_discover.side_effect = fake_discover_factory([
            'docnote_extract_testpkg',
            'docnote_extract_testpkg._hand_rolled',
            'docnote_extract_testpkg._hand_rolled.imports_3p_metaclass'])
        # Don't forget to mark this, or we won't do anything!
        with mark_special_reftype({
            RefMetadata(
                'docnote_extract_testutils.for_handrolled',
                'ThirdpartyMetaclass'): ReftypeMarker.METACLASS
        }):
            floader = _ExtractionFinderLoader(
                frozenset({'docnote_extract_testpkg'}),
                nostub_packages=frozenset({'pytest'}),
                module_stash_nostub_raw={
                    'pytest': pytest,
                    'docnote_extract_testpkg': docnote_extract_testpkg,
                    'docnote_extract_testpkg._hand_rolled':
                        docnote_extract_testpkg._hand_rolled})

            retval = floader.discover_and_extract()

        to_inspect = retval[
            'docnote_extract_testpkg._hand_rolled.imports_3p_metaclass']
        assert not is_reftyped(to_inspect)
        assert not is_reftyped(to_inspect.Uses3pMetaclass)
        assert has_reftyped_metaclass(to_inspect.Uses3pMetaclass)

    @patch('docnote_extract._extraction.discover_all_modules', autospec=True)
    @purge_cached_testpkg_modules
    def test_inspection_works_with_subclass(self, mock_discover):
        """After installing the import hook and while inspecting a
        module, modules that create classes that inherit from
        third-party base classes must still be inspectable.
        """
        # Mock this out so we don't check literally the entire testpkg
        mock_discover.side_effect = fake_discover_factory([
            'docnote_extract_testpkg',
            'docnote_extract_testpkg._hand_rolled',
            'docnote_extract_testpkg._hand_rolled.subclasses_3p_class'])

        floader = _ExtractionFinderLoader(
            frozenset({'docnote_extract_testpkg'}),
            nostub_packages=frozenset({'pytest'}),
            module_stash_nostub_raw={
                'pytest': pytest,
                'docnote_extract_testpkg': docnote_extract_testpkg,
                'docnote_extract_testpkg._hand_rolled':
                    docnote_extract_testpkg._hand_rolled})

        retval = floader.discover_and_extract()

        to_inspect = retval[
            'docnote_extract_testpkg._hand_rolled.subclasses_3p_class']
        assert not is_reftyped(to_inspect)
        assert not is_reftyped(to_inspect.Uses3pBaseclass)
        assert has_reftyped_base(to_inspect.Uses3pBaseclass)

    @patch('docnote_extract._extraction.discover_all_modules', autospec=True)
    @purge_cached_testpkg_modules
    def test_parent_imports_stubbed(self, mock_discover):
        """After installing the import hook and while inspecting a
        module, imports from that module's parent module must still be
        stubbed.
        """
        # Mock this out so we don't check literally the entire testpkg
        mock_discover.side_effect = fake_discover_factory([
            'docnote_extract_testpkg',
            'docnote_extract_testpkg._hand_rolled',
            'docnote_extract_testpkg._hand_rolled.imports_from_parent'])

        floader = _ExtractionFinderLoader(
            frozenset({'docnote_extract_testpkg'}),
            nostub_packages=frozenset({'pytest'}),
            module_stash_nostub_raw={
                'pytest': pytest,
                'docnote_extract_testpkg': docnote_extract_testpkg,
                'docnote_extract_testpkg._hand_rolled':
                    docnote_extract_testpkg._hand_rolled})

        retval = floader.discover_and_extract()

        to_inspect = retval[
            'docnote_extract_testpkg._hand_rolled.imports_from_parent']
        assert not is_reftyped(to_inspect)
        assert is_reftyped(to_inspect.SOME_CONSTANT)

    @patch('docnote_extract._extraction.discover_all_modules', autospec=True)
    @purge_cached_testpkg_modules
    def test_tracking_imports(self, mock_discover):
        """After installing the import hook and while inspecting a
        module, imports from a nostub module must nonetheless be
        tracked.
        """
        # Mock this out so we don't check literally the entire testpkg
        mock_discover.side_effect = fake_discover_factory([
            'docnote_extract_testpkg',
            'docnote_extract_testpkg._hand_rolled',
            'docnote_extract_testpkg._hand_rolled.imports_from_parent'])

        floader = _ExtractionFinderLoader(
            frozenset({'docnote_extract_testpkg'}),
            nostub_packages=frozenset({'pytest'}),
            # CRITICAL: this is what makes this test unique!
            nostub_firstparty_modules=frozenset({
                'docnote_extract_testpkg._hand_rolled'}),
            module_stash_nostub_raw={
                'pytest': pytest,
                'docnote_extract_testpkg': docnote_extract_testpkg,
                'docnote_extract_testpkg._hand_rolled':
                    docnote_extract_testpkg._hand_rolled})

        retval = floader.discover_and_extract()

        to_inspect = retval[
            'docnote_extract_testpkg._hand_rolled.imports_from_parent']

        assert not is_reftyped(to_inspect)
        assert not is_reftyped(to_inspect.SOME_CONSTANT)
        assert not is_reftyped(to_inspect.RENAMED_SENTINEL)

        registry = to_inspect._docnote_extract_import_tracking_registry
        assert id(to_inspect.RENAMED_SENTINEL) in registry
        assert registry[id(to_inspect.RENAMED_SENTINEL)] == (
            'docnote_extract_testpkg._hand_rolled',
            'SOME_SENTINEL')
