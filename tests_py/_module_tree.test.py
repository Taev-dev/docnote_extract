from __future__ import annotations

from types import ModuleType
from typing import cast

from docnote import DOCNOTE_CONFIG_ATTR_FOR_MODULES
from docnote import DocnoteConfig
from docnote import MarkupLang

from docnote_extract._extraction import ModulePostExtraction
from docnote_extract._module_tree import ModuleTreeNode


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
