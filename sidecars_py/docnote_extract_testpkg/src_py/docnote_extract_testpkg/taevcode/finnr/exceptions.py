# This is a programmatically-vendored code sample
# that has been stubbified (ie, function bodies removed). Do not modify
# it directly; your changes will just be overwritten.

# The original source is:
# PkgSrcSpec(forge='github',
#            repo_id='Taev-dev/finnr',
#            pkg_name='finnr',
#            offset_dest_root_dir='taevcode',
#            root_path='src_py/finnr',
#            commit_hash='5a58ed0fc95b068ae396ce3adea91ca66cabe169',
#            license_paths=set())

# The license of the original project is included in the top level of
# the vendored project directory.

# To regenerate, see sidecars/docnote_extract_testpkg_factory. The
# command is:
# ``uv run python -m docnote_extract_testpkg_factory``.

class FinnrException(Exception):
    """This is used as the base class for all finnr exceptions. It can
    be used as a catchall for all other finnr problems.
    """
class MoneyRequired(FinnrException, TypeError):
    """Raised when you attempted to do math between a ``Money`` object
    and a scalar, in a situation where both objects must be ``Money``s.
    """
class ScalarRequired(FinnrException, TypeError):
    """Raised when you attempted to do math between two ``Money``
    objects in a situation where one of them must be a scalar (``int``,
    ``float``, ``Decimal``, etc).
    """
class MismatchedCurrency(FinnrException, ValueError):
    """Raised when you attempted to do math between two ``Money``
    objects of different currencies.
    """
