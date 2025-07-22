import sys

from docnote_extract._reftypes import has_reftyped_base
from docnote_extract._reftypes import has_reftyped_metaclass
from docnote_extract._reftypes import is_reftyped
from docnote_extract.import_hook import inspect_module
from docnote_extract.import_hook import install_import_hook
from docnote_extract.import_hook import uninstall_import_hook
from docnote_extract.import_hook import use_metaclass_reftype


class TestInstallation:

    def test_uninstall_also_removes_imported_modules(self):
        """Uninstalling the import hook must also remove any stubbed
        modules from sys.modules.
        """
        sys.modules.pop('docnote_extract_testpkg', None)

        install_import_hook()
        try:
            import docnote_extract_testpkg  # noqa: F401
            assert 'docnote_extract_testpkg' in sys.modules

        finally:
            uninstall_import_hook()
        assert 'docnote_extract_testpkg' not in sys.modules

    def test_stubbs_returned_after_installation(self):
        """To ensure park security, imports after installation must be
        escorted by at least one host. Errr, wait, got caught in a
        reverie, wrong thing. After installing the import hook,
        importing a not-under-inspection module must return a stubbed
        module. After uninstallation, the normal module must be
        returned.
        """
        sys.modules.pop('docnote_extract_testpkg', None)

        install_import_hook()
        try:
            import docnote_extract_testpkg
            assert is_reftyped(docnote_extract_testpkg)

        finally:
            uninstall_import_hook()
        import docnote_extract_testpkg
        assert not is_reftyped(docnote_extract_testpkg)

    def test_inspection_leaves_target_unstubbed(self):
        """After installing the import hook and while inspecting a
        module, the returned module (and later imports thereof) must
        return the module being inspected itself, and not a stubbed
        version thereof.
        """
        sys.modules.pop('docnote_extract_testpkg', None)
        sys.modules.pop('docnote_extract_testpkg._hand_rolled', None)

        install_import_hook()
        try:
            with inspect_module(
                'docnote_extract_testpkg._hand_rolled'
            ) as to_inspect:
                import docnote_extract_testpkg._hand_rolled
                assert to_inspect is docnote_extract_testpkg._hand_rolled
                assert not is_reftyped(to_inspect)
                assert to_inspect.SOME_CONSTANT == 7

        finally:
            uninstall_import_hook()

    def test_inspection_works_with_metaclasses(self):
        """After installing the import hook and while inspecting a
        module, modules that create classes using imported third-party
        metaclasses must still be inspectable.
        """
        sys.modules.pop('docnote_extract_testpkg', None)
        sys.modules.pop('docnote_extract_testpkg._hand_rolled', None)
        sys.modules.pop(
            'docnote_extract_testpkg._hand_rolled.imports_3p_metaclass', None)

        install_import_hook()
        try:
            # Don't forget this! This is critical!
            with use_metaclass_reftype(
                'example:ThirdpartyMetaclass'
            ), inspect_module(
                'docnote_extract_testpkg._hand_rolled.imports_3p_metaclass'
            ) as to_inspect:
                assert not is_reftyped(to_inspect)
                assert not is_reftyped(to_inspect.Uses3pMetaclass)
                assert has_reftyped_metaclass(to_inspect.Uses3pMetaclass)

        finally:
            uninstall_import_hook()

    def test_inspection_works_with_subclass(self):
        """After installing the import hook and while inspecting a
        module, modules that create classes that inherit from
        third-party base classes must still be inspectable.
        """
        sys.modules.pop('docnote_extract_testpkg', None)
        sys.modules.pop('docnote_extract_testpkg._hand_rolled', None)
        sys.modules.pop(
            'docnote_extract_testpkg._hand_rolled.subclasses_3p_class', None)

        install_import_hook()
        try:
            with inspect_module(
                'docnote_extract_testpkg._hand_rolled.subclasses_3p_class'
            ) as to_inspect:
                assert not is_reftyped(to_inspect)
                assert not is_reftyped(to_inspect.Uses3pBaseclass)
                assert has_reftyped_base(to_inspect.Uses3pBaseclass)

        finally:
            uninstall_import_hook()
