from __future__ import annotations

from types import ModuleType
from types import SimpleNamespace
from typing import cast

import pytest

from docnote_extract._crossrefs import Crossref
from docnote_extract._crossrefs import Crossreffed
from docnote_extract._types import CallableDesc
from docnote_extract._types import ClassDesc
from docnote_extract._types import CrossrefDesc
from docnote_extract._types import DescBase
from docnote_extract._types import ModuleDesc
from docnote_extract._types import ObjClassification
from docnote_extract._types import VariableDesc

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
            (fake_reftype, CrossrefDesc),
            (FakeClass, ClassDesc),
            (fake_coro_gen, CallableDesc),
            (fake_coro, CallableDesc),
            (fake_module, ModuleDesc),
            (fake_func, CallableDesc),
            (fake_gen, CallableDesc),
            (object(), VariableDesc),
            (FakeClass.__add__, CallableDesc),
            (FakeClass.instancemethod, CallableDesc),
            (FakeClass.classmethod_, CallableDesc),
            (FakeClass.staticmethod_, CallableDesc),
            (int.__add__, CallableDesc),])
    def test_get_desc_class(
            self, src_obj, expected_retval: type[DescBase] | None):
        """get_desc_class must return the expected desc class for the
        underlying object, or None if a reftype.
        """
        classification = ObjClassification.from_obj(src_obj)
        assert classification.get_desc_class() is expected_retval
