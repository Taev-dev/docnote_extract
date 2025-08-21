import pytest
from docnote import ReftypeMarker

from docnote_extract import Docnotes
from docnote_extract import SummaryMetadata
from docnote_extract import gather
from docnote_extract._module_tree import SummaryTreeNode
from docnote_extract.crossrefs import Crossref


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
