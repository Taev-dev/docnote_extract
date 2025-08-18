from __future__ import annotations

from collections.abc import Callable

import pytest
from docnote import DocnoteConfig

from docnote_extract._module_tree import ConfiguredModuleTreeNode
from docnote_extract._module_tree import SummaryTreeNode
from docnote_extract._summarization import DescMetadata
from docnote_extract._types import ClassDesc
from docnote_extract._types import ModuleDesc
from docnote_extract._types import Singleton
from docnote_extract._types import VariableDesc
from docnote_extract.filtering import _conventionally_private
from docnote_extract.filtering import _is_dunder
from docnote_extract.filtering import filter_canonical_ownership
from docnote_extract.filtering import filter_module_summaries
from docnote_extract.filtering import filter_private_summaries
from docnote_extract.normalization import NormalizedObj
from docnote_extract.normalization import TypeSpec


class TestFilterModuleSummaries:

    def test_root_filtered(self):
        """When the root node is supposed to be filtered out, its
        metadata must be assigned accordingly.

        This also ensures that the modification must happen in-place,
        and that the values are set both on the module summary and on
        the summary tree node.
        """
        target_metadata = DescMetadata()
        configured_root = ConfiguredModuleTreeNode(
            '_foo',
            '_foo',
            {},
            effective_config=DocnoteConfig(),)
        summary_root = SummaryTreeNode(
            '_foo',
            '_foo',
            {},
            module_summary=ModuleDesc(
                crossref=None,
                ordering_index=None,
                child_groups=(),
                parent_group_name=None,
                metadata=target_metadata,
                name='_foo',
                dunder_all=None,
                docstring=None,
                members=frozenset()))

        assert not hasattr(target_metadata, 'to_document')
        assert summary_root.to_document is None
        retval = filter_module_summaries(summary_root, configured_root)

        assert retval is None
        assert target_metadata.to_document is False
        assert summary_root.to_document is False

    def test_inferred_with_nesting(self):
        """Without any overrides, inferred inclusion should be done
        recursively across all modules.

        This also ensures that the modification must happen in-place,
        and that the values are set both on the module summary and on
        the summary tree node.
        """
        foo_metadata = DescMetadata()
        foobar_metadata = DescMetadata()
        foobarbaz_metadata = DescMetadata()
        configured_root = ConfiguredModuleTreeNode(
            'foo',
            'foo',
            {'bar': ConfiguredModuleTreeNode(
                'foo.bar',
                'bar',
                {'baz': ConfiguredModuleTreeNode(
                    'foo.bar.baz',
                    'baz',
                    effective_config=DocnoteConfig(),)},
                effective_config=DocnoteConfig(),)},
            effective_config=DocnoteConfig(),)
        summary_root = SummaryTreeNode(
            'foo',
            'foo',
            {'bar': SummaryTreeNode(
                'foo.bar',
                'bar',
                {'baz': SummaryTreeNode(
                    'foo.bar.baz',
                    'baz',
                    module_summary=ModuleDesc(
                        crossref=None,
                        ordering_index=None,
                        child_groups=(),
                        parent_group_name=None,
                        metadata=foobarbaz_metadata,
                        name='foo.bar.baz',
                        dunder_all=None,
                        docstring=None,
                        members=frozenset()),)},
                module_summary=ModuleDesc(
                    crossref=None,
                    ordering_index=None,
                    child_groups=(),
                    parent_group_name=None,
                    metadata=foobar_metadata,
                    name='foo.bar',
                    dunder_all=None,
                    docstring=None,
                    members=frozenset()),)},
            module_summary=ModuleDesc(
                crossref=None,
                ordering_index=None,
                child_groups=(),
                parent_group_name=None,
                metadata=foo_metadata,
                name='foo',
                dunder_all=None,
                docstring=None,
                members=frozenset()))

        assert summary_root.to_document is None
        assert not hasattr(foo_metadata, 'to_document')
        assert not hasattr(foobar_metadata, 'to_document')
        assert not hasattr(foobarbaz_metadata, 'to_document')
        retval = filter_module_summaries(summary_root, configured_root)

        assert retval is None
        assert foo_metadata.to_document is True
        assert summary_root.to_document is True
        assert foobar_metadata.to_document is True
        assert (summary_root / 'bar').to_document is True
        assert foobarbaz_metadata.to_document is True
        assert (summary_root / 'bar' / 'baz').to_document is True

    def test_without_configs(self):
        """Without config overrides, inclusion rules must simply follow
        python conventions.
        """
        foo_metadata = DescMetadata()
        foobar_metadata = DescMetadata()
        foobarbaz_metadata = DescMetadata()
        configured_root = ConfiguredModuleTreeNode(
            'foo',
            'foo',
            {'bar': ConfiguredModuleTreeNode(
                'foo.bar',
                'bar',
                {'_baz': ConfiguredModuleTreeNode(
                    'foo.bar._baz',
                    '_baz',
                    effective_config=DocnoteConfig(),)},
                effective_config=DocnoteConfig(),)},
            effective_config=DocnoteConfig(),)
        summary_root = SummaryTreeNode(
            'foo',
            'foo',
            {'bar': SummaryTreeNode(
                'foo.bar',
                'bar',
                {'_baz': SummaryTreeNode(
                    'foo.bar._baz',
                    '_baz',
                    module_summary=ModuleDesc(
                        crossref=None,
                        ordering_index=None,
                        child_groups=(),
                        parent_group_name=None,
                        metadata=foobarbaz_metadata,
                        name='foo.bar._baz',
                        dunder_all=None,
                        docstring=None,
                        members=frozenset()),)},
                module_summary=ModuleDesc(
                    crossref=None,
                    ordering_index=None,
                    child_groups=(),
                    parent_group_name=None,
                    metadata=foobar_metadata,
                    name='foo.bar',
                    dunder_all=None,
                    docstring=None,
                    members=frozenset()),)},
            module_summary=ModuleDesc(
                crossref=None,
                ordering_index=None,
                child_groups=(),
                parent_group_name=None,
                metadata=foo_metadata,
                name='foo',
                dunder_all=None,
                docstring=None,
                members=frozenset()))

        filter_module_summaries(summary_root, configured_root)

        assert foo_metadata.to_document is True
        assert foobar_metadata.to_document is True
        assert foobarbaz_metadata.to_document is False

    def test_silenced_child(self):
        """The public child of a private parent must also have its
        ``to_document`` set to False.
        """
        foo_metadata = DescMetadata()
        foobar_metadata = DescMetadata()
        foobarbaz_metadata = DescMetadata()
        configured_root = ConfiguredModuleTreeNode(
            'foo',
            'foo',
            {'_bar': ConfiguredModuleTreeNode(
                'foo._bar',
                '_bar',
                {'baz': ConfiguredModuleTreeNode(
                    'foo._bar.baz',
                    'baz',
                    effective_config=DocnoteConfig(),)},
                effective_config=DocnoteConfig(),)},
            effective_config=DocnoteConfig(),)
        summary_root = SummaryTreeNode(
            'foo',
            'foo',
            {'_bar': SummaryTreeNode(
                'foo._bar',
                '_bar',
                {'baz': SummaryTreeNode(
                    'foo._bar.baz',
                    'baz',
                    module_summary=ModuleDesc(
                        crossref=None,
                        ordering_index=None,
                        child_groups=(),
                        parent_group_name=None,
                        metadata=foobarbaz_metadata,
                        name='foo._bar.baz',
                        dunder_all=None,
                        docstring=None,
                        members=frozenset()),)},
                module_summary=ModuleDesc(
                    crossref=None,
                    ordering_index=None,
                    child_groups=(),
                    parent_group_name=None,
                    metadata=foobar_metadata,
                    name='foo._bar',
                    dunder_all=None,
                    docstring=None,
                    members=frozenset()),)},
            module_summary=ModuleDesc(
                crossref=None,
                ordering_index=None,
                child_groups=(),
                parent_group_name=None,
                metadata=foo_metadata,
                name='foo',
                dunder_all=None,
                docstring=None,
                members=frozenset()))

        filter_module_summaries(summary_root, configured_root)

        assert foo_metadata.to_document is True
        assert foobar_metadata.to_document is False
        assert foobarbaz_metadata.to_document is False

    def test_override_force_include(self):
        """When an attached config is marked include_in_docs=True, it
        it must be included in the result, regardless of python
        conventions.
        """
        foo_metadata = DescMetadata()
        foobar_metadata = DescMetadata()
        foobarbaz_metadata = DescMetadata()
        configured_root = ConfiguredModuleTreeNode(
            'foo',
            'foo',
            {'_bar': ConfiguredModuleTreeNode(
                'foo._bar',
                '_bar',
                {'baz': ConfiguredModuleTreeNode(
                    'foo._bar.baz',
                    'baz',
                    effective_config=DocnoteConfig(),)},
                effective_config=DocnoteConfig(include_in_docs=True),)},
            effective_config=DocnoteConfig(),)
        summary_root = SummaryTreeNode(
            'foo',
            'foo',
            {'_bar': SummaryTreeNode(
                'foo._bar',
                '_bar',
                {'baz': SummaryTreeNode(
                    'foo._bar.baz',
                    'baz',
                    module_summary=ModuleDesc(
                        crossref=None,
                        ordering_index=None,
                        child_groups=(),
                        parent_group_name=None,
                        metadata=foobarbaz_metadata,
                        name='foo._bar.baz',
                        dunder_all=None,
                        docstring=None,
                        members=frozenset()),)},
                module_summary=ModuleDesc(
                    crossref=None,
                    ordering_index=None,
                    child_groups=(),
                    parent_group_name=None,
                    metadata=foobar_metadata,
                    name='foo._bar',
                    dunder_all=None,
                    docstring=None,
                    members=frozenset()),)},
            module_summary=ModuleDesc(
                crossref=None,
                ordering_index=None,
                child_groups=(),
                parent_group_name=None,
                metadata=foo_metadata,
                name='foo',
                dunder_all=None,
                docstring=None,
                members=frozenset()))

        filter_module_summaries(summary_root, configured_root)

        assert foo_metadata.to_document is True
        assert foobar_metadata.to_document is True
        assert foobarbaz_metadata.to_document is True

    def test_override_force_exclude(self):
        """When an attached config is marked include_in_docs=False, it
        it must be excluded from the result, regardless of python
        conventions.
        """
        foo_metadata = DescMetadata()
        foobar_metadata = DescMetadata()
        foobarbaz_metadata = DescMetadata()
        configured_root = ConfiguredModuleTreeNode(
            'foo',
            'foo',
            {'bar': ConfiguredModuleTreeNode(
                'foo.bar',
                'bar',
                {'baz': ConfiguredModuleTreeNode(
                    'foo.bar.baz',
                    'baz',
                    effective_config=DocnoteConfig(),)},
                effective_config=DocnoteConfig(include_in_docs=False),)},
            effective_config=DocnoteConfig(),)
        summary_root = SummaryTreeNode(
            'foo',
            'foo',
            {'bar': SummaryTreeNode(
                'foo.bar',
                'bar',
                {'baz': SummaryTreeNode(
                    'foo.bar.baz',
                    'baz',
                    module_summary=ModuleDesc(
                        crossref=None,
                        ordering_index=None,
                        child_groups=(),
                        parent_group_name=None,
                        metadata=foobarbaz_metadata,
                        name='foo.bar.baz',
                        dunder_all=None,
                        docstring=None,
                        members=frozenset()),)},
                module_summary=ModuleDesc(
                    crossref=None,
                    ordering_index=None,
                    child_groups=(),
                    parent_group_name=None,
                    metadata=foobar_metadata,
                    name='foo.bar',
                    dunder_all=None,
                    docstring=None,
                    members=frozenset()),)},
            module_summary=ModuleDesc(
                crossref=None,
                ordering_index=None,
                child_groups=(),
                parent_group_name=None,
                metadata=foo_metadata,
                name='foo',
                dunder_all=None,
                docstring=None,
                members=frozenset()))

        filter_module_summaries(summary_root, configured_root)

        assert foo_metadata.to_document is True
        assert foobar_metadata.to_document is False
        assert foobarbaz_metadata.to_document is False

    def test_module_members_unaffected(self):
        """The members within filtered module summary must not have
        their ``to_document`` value set.
        """
        foo_metadata = DescMetadata()
        foobar_metadata = DescMetadata()
        configured_root = ConfiguredModuleTreeNode(
            '_foo',
            '_foo',
            {},
            effective_config=DocnoteConfig(),)
        summary_root = SummaryTreeNode(
            '_foo',
            '_foo',
            {},
            module_summary=ModuleDesc(
                crossref=None,
                ordering_index=None,
                child_groups=(),
                parent_group_name=None,
                metadata=foo_metadata,
                name='_foo',
                dunder_all=None,
                docstring=None,
                members=frozenset({VariableDesc(
                    name='bar',
                    typespec=None,
                    notes=(),
                    crossref=None,
                    ordering_index=None,
                    child_groups=(),
                    parent_group_name=None,
                    metadata=foobar_metadata)})))

        filter_module_summaries(summary_root, configured_root)

        assert not hasattr(foobar_metadata, 'to_document')


class TestFilterCanonicalOwnership:

    def test_inplace_and_recursive(self):
        """Filtering must be done in-place by assigning the ``disown``
        attribute, and the filter method must return None. The value
        must be applied recursively to all child summaries (but not the
        module).
        """
        foo_metadata = DescMetadata()
        foo_metadata.canonical_module = 'foo'
        foobar_metadata = DescMetadata()
        foobar_metadata.canonical_module = None
        foobarbaz_metadata = DescMetadata()
        foobarbaz_metadata.canonical_module = None
        summary = ModuleDesc(
                crossref=None,
                ordering_index=None,
                child_groups=(),
                parent_group_name=None,
                metadata=foo_metadata,
                name='foo',
                dunder_all=None,
                docstring=None,
                members=frozenset({ClassDesc(
                    name='bar',
                    metaclass=None,
                    crossref=None,
                    ordering_index=None,
                    child_groups=(),
                    parent_group_name=None,
                    docstring=None,
                    bases=(),
                    metadata=foobar_metadata,
                    members=frozenset({VariableDesc(
                        name='baz',
                        typespec=None,
                        notes=(),
                        crossref=None,
                        ordering_index=None,
                        child_groups=(),
                        parent_group_name=None,
                        metadata=foobarbaz_metadata)}))}))

        assert not hasattr(foo_metadata, 'disowned')
        assert not hasattr(foobar_metadata, 'disowned')
        assert not hasattr(foobarbaz_metadata, 'disowned')
        retval = filter_canonical_ownership(summary)

        assert retval is None
        assert foo_metadata.disowned is False
        assert foobar_metadata.disowned is True
        assert foobarbaz_metadata.disowned is True

    def test_unknown_origins_no_override(self):
        """A normalized object with no known origin must be removed
        from the result when remove_unknown_origins == True.
        """
        foo_metadata = DescMetadata()
        foo_metadata.canonical_module = 'foo'
        foobar_metadata = DescMetadata()
        foobar_metadata.canonical_module = None
        summary = ModuleDesc(
                crossref=None,
                ordering_index=None,
                child_groups=(),
                parent_group_name=None,
                metadata=foo_metadata,
                name='foo',
                dunder_all=None,
                docstring=None,
                members=frozenset({VariableDesc(
                    name='bar',
                    typespec=None,
                    notes=(),
                    crossref=None,
                    ordering_index=None,
                    child_groups=(),
                    parent_group_name=None,
                    metadata=foobar_metadata)}))

        filter_canonical_ownership(summary)

        assert foo_metadata.disowned is False
        assert foobar_metadata.disowned is True

    def test_known_origin_match(self):
        """A normalized object with a known origin matching the passed
        module must be included in the result.
        """
        foo_metadata = DescMetadata()
        foo_metadata.canonical_module = 'foo'
        foobar_metadata = DescMetadata()
        foobar_metadata.canonical_module = 'foo'
        summary = ModuleDesc(
                crossref=None,
                ordering_index=None,
                child_groups=(),
                parent_group_name=None,
                metadata=foo_metadata,
                name='foo',
                dunder_all=None,
                docstring=None,
                members=frozenset({VariableDesc(
                    name='bar',
                    typespec=None,
                    notes=(),
                    crossref=None,
                    ordering_index=None,
                    child_groups=(),
                    parent_group_name=None,
                    metadata=foobar_metadata)}))

        filter_canonical_ownership(summary)

        assert foo_metadata.disowned is False
        assert foobar_metadata.disowned is False

    def test_known_origin_nomatch(self):
        """A normalized object with a known origin that doesn't match
        the passed module must not be included in the result.
        """
        foo_metadata = DescMetadata()
        foo_metadata.canonical_module = 'foo'
        foobar_metadata = DescMetadata()
        foobar_metadata.canonical_module = 'oof'
        summary = ModuleDesc(
                crossref=None,
                ordering_index=None,
                child_groups=(),
                parent_group_name=None,
                metadata=foo_metadata,
                name='foo',
                dunder_all=None,
                docstring=None,
                members=frozenset({VariableDesc(
                    name='bar',
                    typespec=None,
                    notes=(),
                    crossref=None,
                    ordering_index=None,
                    child_groups=(),
                    parent_group_name=None,
                    metadata=foobar_metadata)}))

        filter_canonical_ownership(summary)

        assert foo_metadata.disowned is False
        assert foobar_metadata.disowned is True

    def test_known_origin_nomatch_config(self):
        """A normalized object with a known origin that doesn't match
        the passed module must not be included in the result, even if
        it defines a config with include_in_docs=True.
        """
        foo_metadata = DescMetadata()
        foo_metadata.canonical_module = 'foo'
        foobar_metadata = DescMetadata()
        foobar_metadata.canonical_module = 'oof'
        summary = ModuleDesc(
                crossref=None,
                ordering_index=None,
                child_groups=(),
                parent_group_name=None,
                metadata=foo_metadata,
                name='foo',
                dunder_all=None,
                docstring=None,
                members=frozenset({VariableDesc(
                    name='bar',
                    typespec=None,
                    notes=(),
                    crossref=None,
                    ordering_index=None,
                    child_groups=(),
                    parent_group_name=None,
                    metadata=foobar_metadata)}))

        filter_canonical_ownership(summary)

        assert foo_metadata.disowned is False
        assert foobar_metadata.disowned is True


class TestFilterPrivateSummaries:

    def test_inplace_and_recursive(self):
        """The ``to_document`` attribute must be set inplace on the
        existing metadata objects, and it must be done recursively on
        everything in the module.
        """
        foo_metadata = DescMetadata()
        foo_metadata.canonical_module = 'foo'
        foo_metadata.extracted_inclusion = None
        foobar_metadata = DescMetadata()
        foobar_metadata.canonical_module = None
        foobar_metadata.extracted_inclusion = None
        foobarbaz_metadata = DescMetadata()
        foobarbaz_metadata.canonical_module = None
        foobarbaz_metadata.extracted_inclusion = None
        summary = ModuleDesc(
                crossref=None,
                ordering_index=None,
                child_groups=(),
                parent_group_name=None,
                metadata=foo_metadata,
                name='foo',
                dunder_all=None,
                docstring=None,
                members=frozenset({ClassDesc(
                    name='bar',
                    metaclass=None,
                    crossref=None,
                    ordering_index=None,
                    child_groups=(),
                    parent_group_name=None,
                    docstring=None,
                    bases=(),
                    metadata=foobar_metadata,
                    members=frozenset({VariableDesc(
                        name='baz',
                        typespec=None,
                        notes=(),
                        crossref=None,
                        ordering_index=None,
                        child_groups=(),
                        parent_group_name=None,
                        metadata=foobarbaz_metadata)}))}))

        assert not hasattr(foo_metadata, 'to_document')
        assert not hasattr(foobar_metadata, 'to_document')
        assert not hasattr(foobarbaz_metadata, 'to_document')
        retval = filter_private_summaries(summary)

        assert retval is None
        assert not hasattr(foo_metadata, 'to_document')
        assert foobar_metadata.to_document is True
        assert foobarbaz_metadata.to_document is True

    def test_without_configs(self):
        """Without config overrides, inclusion rules must simply follow
        python conventions.
        """
        foo_metadata = DescMetadata()
        foo_metadata.canonical_module = 'foo'
        foo_metadata.extracted_inclusion = None
        foobar_metadata = DescMetadata()
        foobar_metadata.canonical_module = None
        foobar_metadata.extracted_inclusion = None
        foorab_metadata = DescMetadata()
        foorab_metadata.canonical_module = None
        foorab_metadata.extracted_inclusion = None
        summary = ModuleDesc(
                crossref=None,
                ordering_index=None,
                child_groups=(),
                parent_group_name=None,
                metadata=foo_metadata,
                name='foo',
                dunder_all=None,
                docstring=None,
                members=frozenset({
                    VariableDesc(
                        name='bar',
                        typespec=None,
                        notes=(),
                        crossref=None,
                        ordering_index=None,
                        child_groups=(),
                        parent_group_name=None,
                        metadata=foobar_metadata),
                    VariableDesc(
                        name='_rab',
                        typespec=None,
                        notes=(),
                        crossref=None,
                        ordering_index=None,
                        child_groups=(),
                        parent_group_name=None,
                        metadata=foorab_metadata)}))

        filter_private_summaries(summary)

        assert foobar_metadata.to_document is True
        assert foorab_metadata.to_document is False

    def test_override_force_include(self):
        """When an attached config is marked include_in_docs=True, it
        it must be included in the result, regardless of python
        conventions.
        """
        foo_metadata = DescMetadata()
        foo_metadata.canonical_module = 'foo'
        foo_metadata.extracted_inclusion = None
        foobar_metadata = DescMetadata()
        foobar_metadata.canonical_module = None
        foobar_metadata.extracted_inclusion = None
        foorab_metadata = DescMetadata()
        foorab_metadata.canonical_module = None
        foorab_metadata.extracted_inclusion = True
        summary = ModuleDesc(
                crossref=None,
                ordering_index=None,
                child_groups=(),
                parent_group_name=None,
                metadata=foo_metadata,
                name='foo',
                dunder_all=None,
                docstring=None,
                members=frozenset({
                    VariableDesc(
                        name='bar',
                        typespec=None,
                        notes=(),
                        crossref=None,
                        ordering_index=None,
                        child_groups=(),
                        parent_group_name=None,
                        metadata=foobar_metadata),
                    VariableDesc(
                        name='_rab',
                        typespec=None,
                        notes=(),
                        crossref=None,
                        ordering_index=None,
                        child_groups=(),
                        parent_group_name=None,
                        metadata=foorab_metadata)}))

        filter_private_summaries(summary)

        assert foobar_metadata.to_document is True
        assert foorab_metadata.to_document is True

    def test_override_force_exclude(self):
        """When an attached config is marked include_in_docs=False, it
        it must be excluded from the result, regardless of python
        conventions.
        """
        foo_metadata = DescMetadata()
        foo_metadata.canonical_module = 'foo'
        foo_metadata.extracted_inclusion = None
        foobar_metadata = DescMetadata()
        foobar_metadata.canonical_module = None
        foobar_metadata.extracted_inclusion = False
        foorab_metadata = DescMetadata()
        foorab_metadata.canonical_module = None
        foorab_metadata.extracted_inclusion = None
        summary = ModuleDesc(
                crossref=None,
                ordering_index=None,
                child_groups=(),
                parent_group_name=None,
                metadata=foo_metadata,
                name='foo',
                dunder_all=None,
                docstring=None,
                members=frozenset({
                    VariableDesc(
                        name='bar',
                        typespec=None,
                        notes=(),
                        crossref=None,
                        ordering_index=None,
                        child_groups=(),
                        parent_group_name=None,
                        metadata=foobar_metadata),
                    VariableDesc(
                        name='_rab',
                        typespec=None,
                        notes=(),
                        crossref=None,
                        ordering_index=None,
                        child_groups=(),
                        parent_group_name=None,
                        metadata=foorab_metadata)}))

        filter_private_summaries(summary)

        assert foobar_metadata.to_document is False
        assert foorab_metadata.to_document is False

    def test_dunder_included(self):
        """Absent any config overrides, dunders with a known module
        outside of the stdlib must be included in the result.
        """
        foo_metadata = DescMetadata()
        foo_metadata.canonical_module = 'foo'
        foo_metadata.extracted_inclusion = None
        foobar_metadata = DescMetadata()
        foobar_metadata.canonical_module = 'foo'
        foobar_metadata.extracted_inclusion = None
        fooadd_metadata = DescMetadata()
        fooadd_metadata.canonical_module = 'foo'
        fooadd_metadata.extracted_inclusion = None
        summary = ModuleDesc(
                crossref=None,
                ordering_index=None,
                child_groups=(),
                parent_group_name=None,
                metadata=foo_metadata,
                name='foo',
                dunder_all=None,
                docstring=None,
                members=frozenset({
                    # Note that this wouldn't actually be a variable, but it
                    # doesn't matter for this test. What matters is that we
                    # have a quick and easy summary with an assigned canonical
                    # module in the metadata. I mean, it also doesn't make
                    # sense to have an __add__ within a module. Again, doesn't
                    # matter!
                    VariableDesc(
                        name='__add__',
                        typespec=None,
                        notes=(),
                        crossref=None,
                        ordering_index=None,
                        child_groups=(),
                        parent_group_name=None,
                        metadata=fooadd_metadata),
                    VariableDesc(
                        name='__bar__',
                        typespec=None,
                        notes=(),
                        crossref=None,
                        ordering_index=None,
                        child_groups=(),
                        parent_group_name=None,
                        metadata=foobar_metadata)}))

        filter_private_summaries(summary)

        assert foobar_metadata.to_document is True
        assert fooadd_metadata.to_document is True

    def test_dunder_excluded(self):
        """Absent any config overrides, dunders without a known module,
        or with a module source from within the stdlib, must be excluded
        from the result.
        """
        foo_metadata = DescMetadata()
        foo_metadata.canonical_module = 'foo'
        foo_metadata.extracted_inclusion = None
        foobar_metadata = DescMetadata()
        foobar_metadata.canonical_module = None
        foobar_metadata.extracted_inclusion = None
        foodir_metadata = DescMetadata()
        foodir_metadata.canonical_module = 'typing'
        foodir_metadata.extracted_inclusion = None
        fooinit_metadata = DescMetadata()
        fooinit_metadata.canonical_module = None
        fooinit_metadata.extracted_inclusion = None
        summary = ModuleDesc(
                crossref=None,
                ordering_index=None,
                child_groups=(),
                parent_group_name=None,
                metadata=foo_metadata,
                name='foo',
                dunder_all=None,
                docstring=None,
                members=frozenset({
                    # Note that this wouldn't actually be a variable, but it
                    # doesn't matter for this test. What matters is that we
                    # have a quick and easy summary with an assigned canonical
                    # module in the metadata. I mean, it also doesn't make
                    # sense to have an __add__ within a module. Again, doesn't
                    # matter!
                    VariableDesc(
                        name='__dir__',
                        typespec=None,
                        notes=(),
                        crossref=None,
                        ordering_index=None,
                        child_groups=(),
                        parent_group_name=None,
                        metadata=foodir_metadata),
                    VariableDesc(
                        name='__bar__',
                        typespec=None,
                        notes=(),
                        crossref=None,
                        ordering_index=None,
                        child_groups=(),
                        parent_group_name=None,
                        metadata=foobar_metadata),
                    VariableDesc(
                        name='__init__',
                        typespec=None,
                        notes=(),
                        crossref=None,
                        ordering_index=None,
                        child_groups=(),
                        parent_group_name=None,
                        metadata=fooinit_metadata)}))

        filter_private_summaries(summary)

        assert foobar_metadata.to_document is False
        assert foodir_metadata.to_document is False
        assert fooinit_metadata.to_document is False


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


@pytest.mark.parametrize(
    'name,expected_retval',
    [
        ('_foo', False),
        ('__foo', False),
        ('__foo__', True),
        ('foo', False),
        ('foo_', False),])
def test_is_dunder(name: str, expected_retval):
    """Spot-checks: _is_dunder() must actually match the convention.
    """
    assert _is_dunder(name) == expected_retval
