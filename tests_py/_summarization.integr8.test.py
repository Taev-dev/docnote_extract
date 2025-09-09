from __future__ import annotations

from docnote_extract._extraction import _ExtractionFinderLoader
from docnote_extract._module_tree import ConfiguredModuleTreeNode
from docnote_extract._summarization import SummaryMetadata
from docnote_extract._summarization import summarize_module
from docnote_extract.crossrefs import GetattrTraversal
from docnote_extract.normalization import NormalizedConcreteType
from docnote_extract.normalization import NormalizedUnionType
from docnote_extract.normalization import normalize_module_dict
from docnote_extract.summaries import CallableSummary
from docnote_extract.summaries import ClassSummary
from docnote_extract.summaries import ModuleSummary
from docnote_extract.summaries import VariableSummary

from docnote_extract_testutils.fixtures import mocked_extraction_discovery
from docnote_extract_testutils.fixtures import purge_cached_testpkg_modules


class TestSummarization:

    # Ideally we'd have better test specificity here (ie, only be testing the
    # summarization code), but it's **much** faster to just grab real values
    # from the testpkg than it is to write a bunch of fakes.
    @mocked_extraction_discovery([
        'docnote_extract_testpkg',
        'docnote_extract_testpkg.taevcode',
        'docnote_extract_testpkg.taevcode.finnr',
        'docnote_extract_testpkg.taevcode.finnr.money',])
    @purge_cached_testpkg_modules
    def test_summarization_with_finnr_money(self):
        """Summarization of the testpkg/taevcode/finnr/money must
        return expected results.
        """
        floader = _ExtractionFinderLoader(
            frozenset({'docnote_extract_testpkg'}),
            nostub_packages=frozenset({'pytest'}),)
        extraction = floader.discover_and_extract()
        module_trees = ConfiguredModuleTreeNode.from_extraction(extraction)
        normalized_objs = normalize_module_dict(
            extraction['docnote_extract_testpkg.taevcode.finnr.money'],
            module_trees['docnote_extract_testpkg'])
        summary = summarize_module(
            extraction['docnote_extract_testpkg.taevcode.finnr.money'],
            normalized_objs,
            module_trees['docnote_extract_testpkg'])

        assert isinstance(summary, ModuleSummary)
        assert isinstance(summary.metadata, SummaryMetadata)

        member_names = {member.name for member in summary.members}
        assert 'Money' in member_names
        assert 'amount_getter' in member_names

        money_summary = summary / GetattrTraversal('Money')
        assert isinstance(money_summary, ClassSummary)
        assert money_summary.crossref is not None
        assert money_summary.crossref.toplevel_name == 'Money'

        money_member_names = {member.name for member in money_summary.members}
        assert 'amount' in money_member_names
        assert 'currency' in money_member_names
        assert 'is_nominal_major' in money_member_names
        assert 'round_to_major' in money_member_names

        rtm_summary = money_summary / GetattrTraversal('round_to_major')
        assert isinstance(rtm_summary, CallableSummary)

    # Ideally we'd have better test specificity here (ie, only be testing the
    # summarization code), but it's **much** faster to just grab real values
    # from the testpkg than it is to write a bunch of fakes.
    @mocked_extraction_discovery([
        'docnote_extract_testpkg',
        'docnote_extract_testpkg.taevcode',
        'docnote_extract_testpkg.taevcode.finnr',
        'docnote_extract_testpkg.taevcode.finnr.currency',])
    @purge_cached_testpkg_modules
    def test_summarization_with_finnr_currency(self):
        """Summarization of the testpkg/taevcode/finnr/currency must
        return expected results.
        """
        floader = _ExtractionFinderLoader(
            frozenset({'docnote_extract_testpkg'}),
            nostub_packages=frozenset({'pytest'}),)
        extraction = floader.discover_and_extract()
        module_trees = ConfiguredModuleTreeNode.from_extraction(extraction)
        normalized_objs = normalize_module_dict(
            extraction['docnote_extract_testpkg.taevcode.finnr.currency'],
            module_trees['docnote_extract_testpkg'])
        summary = summarize_module(
            extraction['docnote_extract_testpkg.taevcode.finnr.currency'],
            normalized_objs,
            module_trees['docnote_extract_testpkg'])

        assert isinstance(summary, ModuleSummary)
        assert isinstance(summary.metadata, SummaryMetadata)

        member_names = {member.name for member in summary.members}
        assert 'Currency' in member_names
        assert '_CurrencyMetadata' in member_names
        assert 'CurrencySet' in member_names

        currency_summary = summary / GetattrTraversal('Currency')
        assert isinstance(currency_summary, ClassSummary)
        currency_member_names = {
            member.name for member in currency_summary.members}
        assert 'code_alpha3' in currency_member_names
        assert 'entities' in currency_member_names
        assert 'is_active' in currency_member_names
        assert 'mint' in currency_member_names
        assert '__post_init__' in currency_member_names

        code_alpha3_summary = currency_summary / GetattrTraversal(
            'code_alpha3')
        assert isinstance(code_alpha3_summary, VariableSummary)

    @mocked_extraction_discovery([
        'docnote_extract_testpkg',
        'docnote_extract_testpkg._hand_rolled',
        'docnote_extract_testpkg._hand_rolled.noteworthy',])
    @purge_cached_testpkg_modules
    def test_unions(self):
        """A class/instance variable defined using an unions (both
        within and outside of an ``Annotated``)
        must be correctly summarized/normalized into a parent typespec
        with each member of the union being a direct child of the
        typespec, and not hidden within a nested ``NormalizedType``.
        """
        floader = _ExtractionFinderLoader(
            frozenset({'docnote_extract_testpkg'}),
            nostub_packages=frozenset({'pytest'}),)
        extraction = floader.discover_and_extract()
        module_trees = ConfiguredModuleTreeNode.from_extraction(extraction)
        normalized_objs = normalize_module_dict(
            extraction['docnote_extract_testpkg._hand_rolled.noteworthy'],
            module_trees['docnote_extract_testpkg'])
        mod_summary = summarize_module(
            extraction['docnote_extract_testpkg._hand_rolled.noteworthy'],
            normalized_objs,
            module_trees['docnote_extract_testpkg'])

        ann_union_summary = mod_summary / GetattrTraversal(
            'HasVarsWithAnnotatedUnion') / GetattrTraversal('foo')
        bare_union_summary = mod_summary / GetattrTraversal(
            'HasVarsWithAnnotatedUnion') / GetattrTraversal('bar')
        assert isinstance(ann_union_summary, VariableSummary)
        assert isinstance(bare_union_summary, VariableSummary)

        assert bare_union_summary.typespec is not None
        assert isinstance(
            bare_union_summary.typespec.normtype,
            NormalizedUnionType)
        assert len(bare_union_summary.typespec.normtype.normtypes) == 2
        bare_type1, bare_type2 = bare_union_summary.typespec.normtype.normtypes
        assert isinstance(bare_type1, NormalizedConcreteType)
        assert isinstance(bare_type2, NormalizedConcreteType)
        assert {
            bare_type1.primary.toplevel_name,
            bare_type2.primary.toplevel_name} == {'int', 'float'}

        assert ann_union_summary.typespec is not None
        assert isinstance(
            ann_union_summary.typespec.normtype,
            NormalizedUnionType)
        assert len(ann_union_summary.typespec.normtype.normtypes) == 2
        ann_type1, ann_type2 = ann_union_summary.typespec.normtype.normtypes
        assert isinstance(ann_type1, NormalizedConcreteType)
        assert isinstance(ann_type2, NormalizedConcreteType)
        assert {
            ann_type1.primary.toplevel_name,
            ann_type2.primary.toplevel_name} == {'int', 'float'}
