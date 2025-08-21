from __future__ import annotations

from types import ModuleType
from types import SimpleNamespace
from typing import cast

import pytest

from docnote_extract.crossrefs import Crossref
from docnote_extract.crossrefs import Crossreffed
from docnote_extract.summaries import CallableSummary
from docnote_extract.summaries import ClassSummary
from docnote_extract.summaries import CrossrefSummary
from docnote_extract.summaries import ModuleSummary
from docnote_extract.summaries import ObjClassification
from docnote_extract.summaries import SummaryBase
from docnote_extract.summaries import VariableSummary

fake_module = ModuleType('foo')
def fake_func(): ...
def fake_gen(): yield
async def fake_coro(): ...
async def fake_coro_gen(): yield
fake_reftype = cast(Crossreffed, SimpleNamespace(
    _docnote_extract_metadata=Crossref(
        module_name='foo', toplevel_name='bar')))


class FakeClass:

    def __add__(self, other): ...
    def instancemethod(self): ...
    @classmethod
    def classmethod_(cls): ...
    @staticmethod
    def staticmethod_(): ...


class TestObjClassification:

    @pytest.mark.parametrize(
        'src_obj,expected_retval',
        [
            (fake_reftype, CrossrefSummary),
            (FakeClass, ClassSummary),
            (fake_coro_gen, CallableSummary),
            (fake_coro, CallableSummary),
            (fake_module, ModuleSummary),
            (fake_func, CallableSummary),
            (fake_gen, CallableSummary),
            (object(), VariableSummary),
            (FakeClass.__add__, CallableSummary),
            (FakeClass.instancemethod, CallableSummary),
            (FakeClass.classmethod_, CallableSummary),
            (FakeClass.staticmethod_, CallableSummary),
            (int.__add__, CallableSummary),])
    def test_get_summary_class(
            self, src_obj, expected_retval: type[SummaryBase] | None):
        """get_summary_class must return the expected summary class for
        the underlying object, or None if a reftype.
        """
        classification = ObjClassification.from_obj(src_obj)
        assert classification.get_summary_class() is expected_retval
