from __future__ import annotations

import pytest
from docnote import DocnoteConfig

from docnote_extract._extraction import ModulePostExtraction
from docnote_extract._types import Singleton
from docnote_extract.discovery import ModuleTreeNode
from docnote_extract.discovery import ModuleTreeNodeHydrated
from docnote_extract.filtering import _conventionally_private
from docnote_extract.filtering import filter_inclusion_rules
from docnote_extract.filtering import filter_module_members
from docnote_extract.filtering import filter_modules
from docnote_extract.normalization import NormalizedObj


class TestFilterModules:

    def test_root_filtered(self):
        """When the root node is supposed to be filtered out, the return
        value must be None.
        """
        root: ModuleTreeNodeHydrated = ModuleTreeNode(
            '_foo',
            '_foo',
            {},
            effective_config=DocnoteConfig(),
            module=ModulePostExtraction('_foo'))

        retval = filter_modules(root)

        assert retval is None

    def test_not_inplace(self):
        """When not filtered out, the return value must be a new object,
        and not an inplace modification of the passed root node.
        """
        root: ModuleTreeNodeHydrated = ModuleTreeNode(
            'foo',
            'foo',
            {},
            effective_config=DocnoteConfig(),
            module=ModulePostExtraction('foo'))

        retval = filter_modules(root)

        assert retval is not None
        assert retval is not root
        assert isinstance(retval, ModuleTreeNode)

    def test_without_configs(self):
        """Without config overrides, inclusion rules must simply follow
        python conventions.
        """
        root: ModuleTreeNodeHydrated = ModuleTreeNode(
            'foo',
            'foo',
            {'bar': ModuleTreeNode(
                'foo.bar',
                'bar',
                {'baz': ModuleTreeNode(
                    'foo.bar._baz',
                    '_baz',
                    effective_config=DocnoteConfig(),
                    module=ModulePostExtraction('_baz'))},
                effective_config=DocnoteConfig(),
                module=ModulePostExtraction('bar'))},
            effective_config=DocnoteConfig(),
            module=ModulePostExtraction('foo'))

        retval = filter_modules(root)

        assert retval is not None
        assert isinstance(retval / 'bar', ModuleTreeNode)
        assert not (retval / 'bar').children

    def test_silenced_child(self):
        """The public child of a private parent must not be included in
        the result.
        """
        root: ModuleTreeNodeHydrated = ModuleTreeNode(
            'foo',
            'foo',
            {'bar': ModuleTreeNode(
                'foo._bar',
                '_bar',
                {'baz': ModuleTreeNode(
                    'foo._bar.baz',
                    'baz',
                    effective_config=DocnoteConfig(),
                    module=ModulePostExtraction('baz'))},
                effective_config=DocnoteConfig(),
                module=ModulePostExtraction('_bar'))},
            effective_config=DocnoteConfig(),
            module=ModulePostExtraction('foo'))

        retval = filter_modules(root)

        assert retval is not None
        assert not retval.children

    def test_override_force_include(self):
        """When an attached config is marked include_in_docs=True, it
        it must be included in the result, regardless of python
        conventions.
        """
        root: ModuleTreeNodeHydrated = ModuleTreeNode(
            'foo',
            'foo',
            {'_bar': ModuleTreeNode(
                'foo._bar',
                '_bar',
                {'baz': ModuleTreeNode(
                    'foo._bar.baz',
                    'baz',
                    effective_config=DocnoteConfig(),
                    module=ModulePostExtraction('baz'))},
                effective_config=DocnoteConfig(include_in_docs=True),
                module=ModulePostExtraction('_bar'))},
            effective_config=DocnoteConfig(),
            module=ModulePostExtraction('foo'))

        retval = filter_modules(root)

        assert retval is not None
        assert retval.children
        assert isinstance(retval / '_bar', ModuleTreeNode)
        assert (retval / '_bar').children

    def test_override_force_exclude(self):
        """When an attached config is marked include_in_docs=False, it
        it must be excluded from the result, regardless of python
        conventions.
        """
        root: ModuleTreeNodeHydrated = ModuleTreeNode(
            'foo',
            'foo',
            {'bar': ModuleTreeNode(
                'foo.bar',
                'bar',
                {'baz': ModuleTreeNode(
                    'foo.bar.baz',
                    'baz',
                    effective_config=DocnoteConfig(),
                    module=ModulePostExtraction('baz'))},
                effective_config=DocnoteConfig(include_in_docs=False),
                module=ModulePostExtraction('bar'))},
            effective_config=DocnoteConfig(),
            module=ModulePostExtraction('foo'))

        retval = filter_modules(root)

        assert retval is not None
        assert not retval.children


class TestFilterModuleMembers:

    def test_not_inplace(self):
        """The returned result must be a new object, not an inplace
        mutation of the passed normalized objects.
        """
        module = ModulePostExtraction('foo')
        normalized_objs = {
            'bar': NormalizedObj(
                4,
                (),
                DocnoteConfig(),
                (),
                int,
                canonical_module=Singleton.UNKNOWN,
                canonical_name=Singleton.UNKNOWN)}

        retval = filter_module_members(module, normalized_objs)

        assert retval is not normalized_objs

    def test_unknown_origins_no_override(self):
        """A normalized object with no known origin must be removed
        from the result when remove_unknown_origins == True.
        """
        module = ModulePostExtraction('foo')
        normalized_objs = {
            'bar': NormalizedObj(
                4,
                (),
                DocnoteConfig(),
                (),
                int,
                canonical_module=Singleton.UNKNOWN,
                canonical_name=Singleton.UNKNOWN)}

        retval = filter_module_members(module, normalized_objs)

        assert not retval

    def test_known_origin_match(self):
        """A normalized object with a known origin matching the passed
        module must be included in the result.
        """
        module = ModulePostExtraction('foo')
        normalized_objs = {
            'bar': NormalizedObj(
                4,
                (),
                DocnoteConfig(),
                (),
                int,
                # Not realistic -- we'd have no way of knowing where an int
                # was from -- but good enough for this test
                canonical_module='foo',
                canonical_name='bar')}

        retval = filter_module_members(module, normalized_objs)

        assert retval
        assert retval == normalized_objs

    def test_known_origin_nomatch(self):
        """A normalized object with a known origin that doesn't match
        the passed module must not be included in the result.
        """
        module = ModulePostExtraction('foo')
        normalized_objs = {
            'bar': NormalizedObj(
                4,
                (),
                DocnoteConfig(),
                (),
                int,
                # Not realistic -- we'd have no way of knowing where an int
                # was from -- but good enough for this test
                canonical_module='oof',
                canonical_name='bar')}

        retval = filter_module_members(module, normalized_objs)

        assert not retval

    def test_known_origin_nomatch_config(self):
        """A normalized object with a known origin that doesn't match
        the passed module must not be included in the result, even if
        it defines a config with include_in_docs=True.
        """
        module = ModulePostExtraction('foo')
        normalized_objs = {
            'bar': NormalizedObj(
                4,
                (),
                DocnoteConfig(include_in_docs=True),
                (),
                int,
                # Not realistic -- we'd have no way of knowing where an int
                # was from -- but good enough for this test
                canonical_module='oof',
                canonical_name='bar')}

        retval = filter_module_members(module, normalized_objs)

        assert not retval


class TestFilterInclusionRules:

    def test_not_inplace(self):
        """The returned result must be a new object, not an inplace
        mutation of the passed normalized objects.
        """
        normalized_objs = {
            'foo': NormalizedObj(
                4,
                (),
                DocnoteConfig(),
                (),
                int,
                canonical_module=Singleton.UNKNOWN,
                canonical_name=Singleton.UNKNOWN)}

        retval = filter_inclusion_rules(normalized_objs)

        assert retval is not normalized_objs

    def test_without_configs(self):
        """Without config overrides, inclusion rules must simply follow
        python conventions.
        """
        normalized_objs = {
            'foo': NormalizedObj(
                4,
                (),
                DocnoteConfig(),
                (),
                int,
                canonical_module=Singleton.UNKNOWN,
                canonical_name=Singleton.UNKNOWN),
            '_bar': NormalizedObj(
                4,
                (),
                DocnoteConfig(),
                (),
                int,
                canonical_module=Singleton.UNKNOWN,
                canonical_name=Singleton.UNKNOWN),}

        retval = filter_inclusion_rules(normalized_objs)

        assert 'foo' in retval
        assert '_bar' not in retval

    def test_override_force_include(self):
        """When an attached config is marked include_in_docs=True, it
        it must be included in the result, regardless of python
        conventions.
        """
        normalized_objs = {
            'foo': NormalizedObj(
                4,
                (),
                DocnoteConfig(),
                (),
                int,
                canonical_module=Singleton.UNKNOWN,
                canonical_name=Singleton.UNKNOWN),
            '_bar': NormalizedObj(
                4,
                (),
                DocnoteConfig(include_in_docs=True),
                (),
                int,
                canonical_module=Singleton.UNKNOWN,
                canonical_name=Singleton.UNKNOWN),}

        retval = filter_inclusion_rules(normalized_objs)

        assert 'foo' in retval
        assert '_bar' in retval

    def test_override_force_exclude(self):
        """When an attached config is marked include_in_docs=False, it
        it must be excluded from the result, regardless of python
        conventions.
        """
        normalized_objs = {
            'foo': NormalizedObj(
                4,
                (),
                DocnoteConfig(include_in_docs=False),
                (),
                int,
                canonical_module=Singleton.UNKNOWN,
                canonical_name=Singleton.UNKNOWN),
            '_bar': NormalizedObj(
                4,
                (),
                DocnoteConfig(),
                (),
                int,
                canonical_module=Singleton.UNKNOWN,
                canonical_name=Singleton.UNKNOWN),}

        retval = filter_inclusion_rules(normalized_objs)

        assert 'foo' not in retval
        assert '_bar' not in retval


@pytest.mark.parametrize(
    'name,expected_retval',
    [
        ('_foo', True),
        ('__foo', True),
        ('__foo__', False),
        ('foo', False),
        ('foo_', False),])
def test_conventionally_private(name: str, expected_retval):
    """Spot-checks: _conventionally_private() must actually match the
    convention.
    """
    assert _conventionally_private(name) == expected_retval
