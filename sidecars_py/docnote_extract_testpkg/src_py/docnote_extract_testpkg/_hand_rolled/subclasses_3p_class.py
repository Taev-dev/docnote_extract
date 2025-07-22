"""We use this module to test that the import hook works correctly for
modules that inherit from third-party classes.
"""
from example import ThirdpartyBaseclass


# Note that even just inheriting from a base might imply a metaclass with
# a param
class Uses3pBaseclass(ThirdpartyBaseclass, foo='oof'):

    def foo(self):
        ...
