from __future__ import annotations

import importlib
from types import ModuleType
from typing import cast
from unittest.mock import patch

import pytest
from docnote import DOCNOTE_CONFIG_ATTR_FOR_MODULES
from docnote import DocnoteConfig
from docnote import MarkupLang

from docnote_extract._extraction import ModulePostExtraction
from docnote_extract.discovery import ModuleTreeNode
from docnote_extract.discovery import eager_import_submodules
from docnote_extract.discovery import validate_config
from docnote_extract.exceptions import InvalidConfig

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

    def test_from_extraction(self):
        """from_extraction must construct a correct tree. It must also
        merge configs correctly across levels.
        """
        fake_extraction = {
            'foo': ModuleType('foo'),
            'foo.bar': ModuleType('foo.bar'),
            'foo.bar.baz': ModuleType('foo.bar.baz'),
            'oof': ModuleType('oof'),
            'oof.rab': ModuleType('oof.rab'),
            'oof.zab': ModuleType('oof.zab')}
        setattr(
            fake_extraction['foo'],
            DOCNOTE_CONFIG_ATTR_FOR_MODULES,
            DocnoteConfig(enforce_known_lang=False))
        setattr(
            fake_extraction['foo.bar'],
            DOCNOTE_CONFIG_ATTR_FOR_MODULES,
            DocnoteConfig(enforce_known_lang=True))
        setattr(
            fake_extraction['foo.bar.baz'],
            DOCNOTE_CONFIG_ATTR_FOR_MODULES,
            DocnoteConfig(markup_lang=MarkupLang.CLEANCOPY))
        fake_extraction = cast(
            dict[str, ModulePostExtraction], fake_extraction)

        root_nodes = ModuleTreeNode.from_extraction(fake_extraction)

        assert len(root_nodes) == 2
        assert 'foo' in root_nodes
        assert 'oof' in root_nodes
        oof_root = root_nodes['oof']
        foo_root = root_nodes['foo']
        assert len(oof_root.children) == 2
        assert len(foo_root.children) == 1
        assert len(foo_root.children['bar'].children) == 1

        assert oof_root.effective_config == DocnoteConfig()
        assert (oof_root / 'rab').effective_config == DocnoteConfig()
        assert foo_root.effective_config == DocnoteConfig(
            enforce_known_lang=False)
        assert (foo_root / 'bar').effective_config == DocnoteConfig(
            enforce_known_lang=True)
        assert (foo_root / 'bar' / 'baz').effective_config == DocnoteConfig(
            enforce_known_lang=True, markup_lang=MarkupLang.CLEANCOPY)

    def test_flattening(self):
        """Flattening a tree from its extraction must reproduce the
        extraction.
        """
        fake_extraction = {
            'foo': ModuleType('foo'),
            'foo.bar': ModuleType('foo.bar'),
            'foo.bar.baz': ModuleType('foo.bar.baz'),
            'oof': ModuleType('oof'),
            'oof.rab': ModuleType('oof.rab'),
            'oof.zab': ModuleType('oof.zab')}
        setattr(
            fake_extraction['foo'],
            DOCNOTE_CONFIG_ATTR_FOR_MODULES,
            DocnoteConfig(enforce_known_lang=False))
        setattr(
            fake_extraction['foo.bar'],
            DOCNOTE_CONFIG_ATTR_FOR_MODULES,
            DocnoteConfig(enforce_known_lang=True))
        setattr(
            fake_extraction['foo.bar.baz'],
            DOCNOTE_CONFIG_ATTR_FOR_MODULES,
            DocnoteConfig(markup_lang=MarkupLang.CLEANCOPY))
        fake_extraction = cast(
            dict[str, ModulePostExtraction], fake_extraction)

        retval = {}
        root_nodes = ModuleTreeNode.from_extraction(fake_extraction)
        for root_node in root_nodes.values():
            retval.update(root_node.flatten())

        assert retval == fake_extraction

    def test_clone_without_children(self):
        """Cloning a node without its children must not include its
        children (... no shit, sherlock), but must preserve everything
        else.
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
            effective_config=DocnoteConfig(markup_lang=MarkupLang.CLEANCOPY))

        clone = tree.clone_without_children()
        assert not clone.children
        assert clone != tree
        tree.children.clear()
        assert clone == tree


class TestValidateConfig:

    def test_no_enforcement(self):
        """A config with no enforcement set must return True."""
        config = DocnoteConfig(enforce_known_lang=False, markup_lang='foobar')
        assert validate_config(config, None) is True

    def test_valid(self):
        """A valid config must return True."""
        config = DocnoteConfig(
            enforce_known_lang=True,
            markup_lang=MarkupLang.CLEANCOPY)
        assert validate_config(config, None) is True

    def test_invalid(self):
        """An invalid config must raise InvalidConfig."""
        config = DocnoteConfig(
            enforce_known_lang=True,
            markup_lang='foobar')

        with pytest.raises(InvalidConfig):
            validate_config(config, None)
