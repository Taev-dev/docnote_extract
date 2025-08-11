from collections.abc import Callable
from importlib import import_module
from typing import cast

from docnote import DocnoteConfig
from docnote import Note

from docnote_extract._extraction import ModulePostExtraction
from docnote_extract.discovery import ModuleTreeNode
from docnote_extract.normalization import NormalizedObj
from docnote_extract.normalization import TypeSpec
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
            import_module('docnote_extract_testutils.fixtures'))
        docnote._docnote_extract_import_tracking_registry = {}
        module_tree = ModuleTreeNode(
            'docnote_extract_testutils',
            'docnote_extract_testutils',
            {'taevcode': ModuleTreeNode(
                'docnote_extract_testutils.fixtures',
                'fixtures',
                effective_config=DocnoteConfig())},
            effective_config=DocnoteConfig())

        normalized = normalize_module_dict(docnote, module_tree)

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
            import_module('docnote_extract_testpkg._hand_rolled'))
        docnote._docnote_extract_import_tracking_registry = {}
        module_tree = ModuleTreeNode(
            'docnote_extract_testpkg',
            'docnote_extract_testpkg',
            {'taevcode': ModuleTreeNode(
                'docnote_extract_testpkg._hand_rolled',
                '_hand_rolled',
                effective_config=DocnoteConfig())},
            effective_config=DocnoteConfig())

        normalized = normalize_module_dict(docnote, module_tree)

        norm_cls = normalized['ThisGetsUsedToTestNormalization']
        assert not norm_cls.annotateds
        assert norm_cls.typespec is None
        assert norm_cls.canonical_module == \
            'docnote_extract_testpkg._hand_rolled'
        assert norm_cls.canonical_name == 'ThisGetsUsedToTestNormalization'

    @purge_cached_testpkg_modules
    def test_bare_annotation(self):
        """A bare annotation defined within the current module must be
        included and assigned the correct canonical origin.
        """
        docnote = cast(
            ModulePostExtraction,
            import_module('docnote_extract_testpkg._hand_rolled'))
        docnote._docnote_extract_import_tracking_registry = {}
        module_tree = ModuleTreeNode(
            'docnote_extract_testpkg',
            'docnote_extract_testpkg',
            {'taevcode': ModuleTreeNode(
                'docnote_extract_testpkg._hand_rolled',
                '_hand_rolled',
                effective_config=DocnoteConfig())},
            effective_config=DocnoteConfig())

        normalized = normalize_module_dict(docnote, module_tree)

        assert 'bare_annotation' in normalized
        norm_bare_anno = normalized['bare_annotation']
        assert not norm_bare_anno.annotateds
        assert norm_bare_anno.typespec == TypeSpec.from_typehint(str)
        assert norm_bare_anno.canonical_module == \
            'docnote_extract_testpkg._hand_rolled'
        assert norm_bare_anno.canonical_name == 'bare_annotation'

    @purge_cached_testpkg_modules
    def test_note(self):
        """A value defined within the module that contains a ``Note``
        annotation must include it within the normalized object's note
        attribute.
        """
        test_module = cast(
            ModulePostExtraction,
            import_module('docnote_extract_testpkg._hand_rolled.noteworthy'))
        test_module._docnote_extract_import_tracking_registry = {}
        module_tree = ModuleTreeNode(
            'docnote_extract_testpkg',
            'docnote_extract_testpkg',
            {'_hand_rolled': ModuleTreeNode(
                'docnote_extract_testpkg._hand_rolled',
                '_hand_rolled',
                {'noteworthy': ModuleTreeNode(
                    'docnote_extract_testpkg._hand_rolled.noteworthy',
                    'noteworthy',
                    effective_config=DocnoteConfig())},
                effective_config=DocnoteConfig())},
            effective_config=DocnoteConfig())

        normalized = normalize_module_dict(test_module, module_tree)

        norm_cfg_attr = normalized['DOCNOTE_CONFIG_ATTR']
        assert not norm_cfg_attr.annotateds
        assert norm_cfg_attr.typespec == TypeSpec.from_typehint(
            str)
        assert len(norm_cfg_attr.notes) == 1
        note, = norm_cfg_attr.notes
        assert note.value.startswith('Docs generation libraries should use ')
        assert norm_cfg_attr.effective_config == DocnoteConfig()

    @purge_cached_testpkg_modules
    def test_config(self):
        """A value defined within the module that contains a
        ``DocnoteConfig`` annotation must include it within the
        normalized object's config attribute.
        """
        test_module = cast(
            ModulePostExtraction,
            import_module('docnote_extract_testpkg._hand_rolled.noteworthy'))
        test_module._docnote_extract_import_tracking_registry = {}
        module_tree = ModuleTreeNode(
            'docnote_extract_testpkg',
            'docnote_extract_testpkg',
            {'_hand_rolled': ModuleTreeNode(
                'docnote_extract_testpkg._hand_rolled',
                '_hand_rolled',
                {'noteworthy': ModuleTreeNode(
                    'docnote_extract_testpkg._hand_rolled.noteworthy',
                    'noteworthy',
                    effective_config=DocnoteConfig())},
                effective_config=DocnoteConfig())},
            effective_config=DocnoteConfig())

        normalized = normalize_module_dict(test_module, module_tree)

        clcnote_attr = normalized['ClcNote']
        assert not clcnote_attr.annotateds
        assert clcnote_attr.typespec == TypeSpec.from_typehint(
            Callable[[str], Note])  # type: ignore
        assert not clcnote_attr.notes
        assert clcnote_attr.effective_config == DocnoteConfig(
            include_in_docs=False)

    @purge_cached_testpkg_modules
    def test_config_stacking(self):
        """A value defined within the module that contains a
        ``DocnoteConfig`` annotation must include it within the
        normalized object's config attribute, and this must be stacked
        on top of the module-level config.
        """
        test_module = cast(
            ModulePostExtraction,
            import_module('docnote_extract_testpkg._hand_rolled.noteworthy'))
        test_module._docnote_extract_import_tracking_registry = {}
        module_tree = ModuleTreeNode(
            'docnote_extract_testpkg',
            'docnote_extract_testpkg',
            {'_hand_rolled': ModuleTreeNode(
                'docnote_extract_testpkg._hand_rolled',
                '_hand_rolled',
                {'noteworthy': ModuleTreeNode(
                    'docnote_extract_testpkg._hand_rolled.noteworthy',
                    'noteworthy',
                    effective_config=DocnoteConfig(enforce_known_lang=False))},
                effective_config=DocnoteConfig())},
            effective_config=DocnoteConfig())

        normalized = normalize_module_dict(test_module, module_tree)

        clcnote_attr = normalized['ClcNote']
        assert not clcnote_attr.annotateds
        assert clcnote_attr.typespec == TypeSpec.from_typehint(
            Callable[[str], Note])  # type: ignore
        assert not clcnote_attr.notes
        assert clcnote_attr.effective_config == DocnoteConfig(
            include_in_docs=False,
            enforce_known_lang=False)

    @purge_cached_testpkg_modules
    def test_config_via_decorator(self):
        """A value defined within the module that contains a
        ``DocnoteConfig`` attached via the ``@docnote`` decorator must
        include it within the normalized object's config attribute.
        """
        test_module = cast(
            ModulePostExtraction,
            import_module('docnote_extract_testpkg._hand_rolled.noteworthy'))
        test_module._docnote_extract_import_tracking_registry = {}
        module_tree = ModuleTreeNode(
            'docnote_extract_testpkg',
            'docnote_extract_testpkg',
            {'_hand_rolled': ModuleTreeNode(
                'docnote_extract_testpkg._hand_rolled',
                '_hand_rolled',
                {'noteworthy': ModuleTreeNode(
                    'docnote_extract_testpkg._hand_rolled.noteworthy',
                    'noteworthy',
                    effective_config=DocnoteConfig())},
                effective_config=DocnoteConfig())},
            effective_config=DocnoteConfig())

        normalized = normalize_module_dict(test_module, module_tree)

        func_attr = normalized['func_with_config']
        assert not func_attr.annotateds
        assert func_attr.typespec is None
        assert not func_attr.notes
        assert func_attr.effective_config == DocnoteConfig(
            include_in_docs=False)
