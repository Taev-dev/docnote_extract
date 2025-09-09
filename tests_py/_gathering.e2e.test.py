import pytest
from docnote import ReftypeMarker

from docnote_extract import Docnotes
from docnote_extract import SummaryMetadata
from docnote_extract import gather
from docnote_extract._module_tree import SummaryTreeNode
from docnote_extract.crossrefs import Crossref
from docnote_extract.crossrefs import GetattrTraversal
from docnote_extract.normalization import NormalizedConcreteType
from docnote_extract.normalization import NormalizedLiteralType
from docnote_extract.normalization import NormalizedUnionType
from docnote_extract.summaries import ClassSummary
from docnote_extract.summaries import VariableSummary


@pytest.fixture(scope='module')
def testpkg_docs() -> Docnotes[SummaryMetadata]:
    """We want to do a bunch of spot checks against the testpkg, but
    we only need to gather it once. Hence, we have a module-scoped
    fixture that returns the gathered ``Docnotes``.
    """
    return gather(
        ['docnote_extract_testpkg'],
        special_reftype_markers={
            Crossref(
                module_name='docnote_extract_testutils.for_handrolled',
                toplevel_name='ThirdpartyMetaclass'):
            ReftypeMarker.METACLASS})


class TestGatheringE2E:

    def test_expected_summaries(self, testpkg_docs: Docnotes[SummaryMetadata]):
        """The gathered result must contain the expected number of
        summaries, and it must contain the summary tree root.
        """
        assert len(testpkg_docs.summaries) == 1
        (pkg_name, tree_root), = testpkg_docs.summaries.items()
        assert pkg_name == 'docnote_extract_testpkg'
        assert isinstance(tree_root, SummaryTreeNode)

    def test_spotcheck_money(self, testpkg_docs: Docnotes[SummaryMetadata]):
        """A spot-check of the finnr money module must match the
        expected results.
        """
        (_, tree_root), = testpkg_docs.summaries.items()
        money_mod_node = tree_root.find(
            'docnote_extract_testpkg.taevcode.finnr.money')
        money_mod_summary = money_mod_node.module_summary
        resulting_names = {
            child.name
            for child in money_mod_summary.members
            if child.metadata.included}
        assert resulting_names == {'amount_getter', 'Money'}

    def test_spotcheck_currency(self, testpkg_docs: Docnotes[SummaryMetadata]):
        """A spot-check of the finnr currency module must match the
        expected results. This is particularly concerned with the
        typespec values.
        """
        (_, tree_root), = testpkg_docs.summaries.items()
        currency_mod_node = tree_root.find(
            'docnote_extract_testpkg.taevcode.finnr.currency')
        currency_mod_summary = currency_mod_node.module_summary
        currency_summary = currency_mod_summary / GetattrTraversal('Currency')
        assert isinstance(currency_summary, ClassSummary)

        name_summary = currency_summary / GetattrTraversal('name')
        assert isinstance(name_summary, VariableSummary)

        assert name_summary.typespec is not None
        assert isinstance(
            name_summary.typespec.normtype,
            NormalizedUnionType)
        assert len(name_summary.typespec.normtype.normtypes) == 2

        normtype1, normtype2 = name_summary.typespec.normtype.normtypes

        if isinstance(normtype1, NormalizedConcreteType):
            concrete_union_member = normtype1
            literal_union_member = normtype2
        else:
            concrete_union_member = normtype2
            literal_union_member = normtype1

        # Note that this also catches the else statement in case the types
        # were completely off
        assert isinstance(concrete_union_member, NormalizedConcreteType)
        assert isinstance(literal_union_member, NormalizedLiteralType)

        assert concrete_union_member.primary.toplevel_name == 'str'
        assert not concrete_union_member.primary.traversals
        assert len(literal_union_member.values) == 1
        literal_value, = literal_union_member.values
        assert isinstance(literal_value, Crossref)
        assert literal_value.toplevel_name == 'Singleton'
        assert literal_value.traversals == (GetattrTraversal('UNKNOWN'),)
