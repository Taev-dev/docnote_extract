import sys

from docnote_extract._reftypes import has_reftyped_base
from docnote_extract._reftypes import has_reftyped_metaclass
from docnote_extract._reftypes import is_reftyped
from docnote_extract.import_hook import inspect_module
from docnote_extract.import_hook import stubbed_imports
from docnote_extract.import_hook import use_metaclass_reftype

from docnote_extract_testutils.fixtures import purge_cached_testpkg_modules


class TestInstallation:

    @purge_cached_testpkg_modules
    def test_uninstall_also_removes_imported_modules(self):
        """Uninstalling the import hook must also remove any stubbed
        modules from sys.modules.
        """
        with stubbed_imports():
            import docnote_extract_testpkg  # noqa: PLC0415, RUF100, F401
            assert 'docnote_extract_testpkg' in sys.modules

        assert 'docnote_extract_testpkg' not in sys.modules

    @purge_cached_testpkg_modules
    def test_stubbs_returned_after_installation(self):
        """To ensure park security, imports after installation must be
        escorted by at least one host. Errr, wait, got caught in a
        reverie, wrong thing. After installing the import hook,
        importing a not-under-inspection module must return a stubbed
        module. After uninstallation, the normal module must be
        returned.
        """
        with stubbed_imports():
            import docnote_extract_testpkg  # noqa: PLC0415, RUF100
            assert is_reftyped(docnote_extract_testpkg)

        import docnote_extract_testpkg  # noqa: PLC0415, RUF100
        assert not is_reftyped(docnote_extract_testpkg)

    @purge_cached_testpkg_modules
    def test_inspection_leaves_target_unstubbed(self):
        """After installing the import hook and while inspecting a
        module, the returned module (and later imports thereof) must
        return the module being inspected itself, and not a stubbed
        version thereof.
        """
        with stubbed_imports(), inspect_module(
            'docnote_extract_testpkg._hand_rolled'
        ) as to_inspect:
            import docnote_extract_testpkg._hand_rolled  # noqa: PLC0415, RUF100
            assert to_inspect is docnote_extract_testpkg._hand_rolled
            assert not is_reftyped(to_inspect)
            assert to_inspect.SOME_CONSTANT == 7

    @purge_cached_testpkg_modules
    def test_inspection_works_with_metaclasses(self):
        """After installing the import hook and while inspecting a
        module, modules that create classes using imported third-party
        metaclasses must still be inspectable.
        """
        # Don't forget use_metaclass_reftype! This is critical!
        with stubbed_imports(), use_metaclass_reftype(
            'example:ThirdpartyMetaclass'
        ), inspect_module(
            'docnote_extract_testpkg._hand_rolled.imports_3p_metaclass'
        ) as to_inspect:
            assert not is_reftyped(to_inspect)
            assert not is_reftyped(to_inspect.Uses3pMetaclass)
            assert has_reftyped_metaclass(to_inspect.Uses3pMetaclass)

    @purge_cached_testpkg_modules
    def test_inspection_works_with_subclass(self):
        """After installing the import hook and while inspecting a
        module, modules that create classes that inherit from
        third-party base classes must still be inspectable.
        """
        with stubbed_imports(), inspect_module(
            'docnote_extract_testpkg._hand_rolled.subclasses_3p_class'
        ) as to_inspect:
            assert not is_reftyped(to_inspect)
            assert not is_reftyped(to_inspect.Uses3pBaseclass)
            assert has_reftyped_base(to_inspect.Uses3pBaseclass)

    @purge_cached_testpkg_modules
    def test_parent_imports_stubbed(self):
        """After installing the import hook and while inspecting a
        module, imports from that module's parent module must still be
        stubbed.
        """
        with stubbed_imports(), inspect_module(
            'docnote_extract_testpkg._hand_rolled.imports_from_parent'
        ) as to_inspect:
            assert not is_reftyped(to_inspect)
            assert is_reftyped(to_inspect.SOME_CONSTANT)
