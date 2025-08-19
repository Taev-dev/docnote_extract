from docnote_extract._crossrefs import Crossref
from docnote_extract._gathering import Docnotes
from docnote_extract._module_tree import SummaryTreeNode
from docnote_extract._summarization import ModuleSummary
from docnote_extract._summarization import SummaryMetadata
from docnote_extract._summarization import VariableSummary


class TestDocnotes:

    def test_is_stdlib(self):
        """A stdlib crossref must return True; otherwise, False.
        """
        docnotes = Docnotes(summaries={
            'foo': SummaryTreeNode(
                'foo',
                'foo',
                {},
                module_summary=ModuleSummary(
                    name='foo',
                    crossref=Crossref(
                        module_name='foo',
                        toplevel_name=None,
                        traversals=()),
                    ordering_index=None,
                    child_groups=(),
                    parent_group_name=None,
                    metadata=SummaryMetadata(),
                    dunder_all=None,
                    docstring=None,
                    members=frozenset({
                        VariableSummary(
                            name='bar',
                            typespec=None,
                            notes=(),
                            crossref=Crossref(
                                module_name='foo',
                                toplevel_name='bar',
                                traversals=()),
                            ordering_index=None,
                            child_groups=(),
                            parent_group_name=None,
                            metadata=SummaryMetadata())})))})

        assert docnotes.is_stdlib(Crossref(
            module_name='typing',
            toplevel_name=None,
            traversals=()))
        assert not docnotes.is_stdlib(Crossref(
            module_name='bar',
            toplevel_name=None,
            traversals=()))

    def test_is_firstparty(self):
        """A firstpary crossref must return True; otherwise, False.
        """
        docnotes = Docnotes(summaries={
            'foo': SummaryTreeNode(
                'foo',
                'foo',
                {},
                module_summary=ModuleSummary(
                    name='foo',
                    crossref=Crossref(
                        module_name='foo',
                        toplevel_name=None,
                        traversals=()),
                    ordering_index=None,
                    child_groups=(),
                    parent_group_name=None,
                    metadata=SummaryMetadata(),
                    dunder_all=None,
                    docstring=None,
                    members=frozenset({
                        VariableSummary(
                            name='bar',
                            typespec=None,
                            notes=(),
                            crossref=Crossref(
                                module_name='foo',
                                toplevel_name='bar',
                                traversals=()),
                            ordering_index=None,
                            child_groups=(),
                            parent_group_name=None,
                            metadata=SummaryMetadata())})))})

        assert not docnotes.is_firstparty(Crossref(
            module_name='bar',
            toplevel_name=None,
            traversals=()))
        assert docnotes.is_firstparty(Crossref(
            module_name='foo',
            toplevel_name=None,
            traversals=()))

    def test_resolve_crossref_happy_case(self):
        """Resolving a crossref must return the expected summary object
        for the happy case.
        """
        var_summary = VariableSummary(
            name='bar',
            typespec=None,
            notes=(),
            crossref=Crossref(
                module_name='foo',
                toplevel_name='bar',
                traversals=()),
            ordering_index=None,
            child_groups=(),
            parent_group_name=None,
            metadata=SummaryMetadata())
        docnotes = Docnotes(summaries={
            'foo': SummaryTreeNode(
                'foo',
                'foo',
                {},
                module_summary=ModuleSummary(
                    name='foo',
                    crossref=Crossref(
                        module_name='foo',
                        toplevel_name=None,
                        traversals=()),
                    ordering_index=None,
                    child_groups=(),
                    parent_group_name=None,
                    metadata=SummaryMetadata(),
                    dunder_all=None,
                    docstring=None,
                    members=frozenset({var_summary})))})

        # Just to get type checking to work
        assert var_summary.crossref is not None
        retval = docnotes.resolve_crossref(var_summary.crossref)

        assert retval is var_summary
