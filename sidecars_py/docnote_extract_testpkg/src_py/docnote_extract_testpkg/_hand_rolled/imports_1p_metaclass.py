"""We use this module to test that the import hook works correctly for
modules that import third-party metaclasses.
"""
from docnote_extract_testpkg._hand_rolled.defines_1p_metaclass import Mcls1p


class Uses1pMetaclass(metaclass=Mcls1p):

    def foo(self):
        ...
