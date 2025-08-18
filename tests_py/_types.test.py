from __future__ import annotations

from types import ModuleType
from types import SimpleNamespace
from typing import cast

import pytest

from docnote_extract._crossrefs import Crossref
from docnote_extract._crossrefs import Crossreffed
from docnote_extract._types import CallableSummary
from docnote_extract._types import ClassSummary
from docnote_extract._types import CrossrefSummary
from docnote_extract._types import ModuleSummary
from docnote_extract._types import ObjClassification
from docnote_extract._types import SummaryBase
from docnote_extract._types import VariableSummary

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
    def test_get_desc_class(
            self, src_obj, expected_retval: type[SummaryBase] | None):
        """get_desc_class must return the expected desc class for the
        underlying object, or None if a reftype.
        """
        classification = ObjClassification.from_obj(src_obj)
        assert classification.get_desc_class() is expected_retval
