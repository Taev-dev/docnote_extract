"""We use this module to test that the import hook works correctly for
modules that import third-party metaclasses.
"""
from example import ThirdpartyMetaclass


class Uses3pMetaclass(metaclass=ThirdpartyMetaclass, foo='oof'):

    def foo(self):
        ...
