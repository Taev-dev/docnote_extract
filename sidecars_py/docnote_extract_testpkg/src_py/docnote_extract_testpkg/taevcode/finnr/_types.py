# This is a programmatically-vendored code sample
# that has been stubbified (ie, function bodies removed). Do not modify
# it directly; your changes will just be overwritten.

# The original source is:
# PkgSrcSpec(forge='github',
#            repo_id='Taev-dev/finnr',
#            pkg_name='finnr',
#            offset_dest_root_dir='taevcode',
#            root_path='src_py/finnr',
#            commit_hash='17cf5230f6f24f968aebe07cb92072ccaa9f0eda',
#            license_paths=set())

# The license of the original project is included in the top level of
# the vendored project directory.

# To regenerate, see sidecars/docnote_extract_testpkg_factory. The
# command is:
# ``uv run python -m docnote_extract_testpkg_factory``.

from __future__ import annotations
from enum import Enum
from typing import Annotated
from typing import Any
from typing import Protocol
from docnote import ClcNote
class Singleton(Enum):
    UNKNOWN = 'unknown'
    MISSING = 'missing'
class DateLike(Protocol):
    """Something is date-like if it includes a year, month, and
    day as attributes. We include this for convenience, so that
    users can bring their own datetime library.
    Note that month and day must both be 1-indexed, ie,
    2025-01-01 would be represented by ``{year: 2025, month: 1,
    day: 1}``.
    """
    year: Annotated[
        int | Any,
        ClcNote('''Must be an int or int-like. Annotated to include
            ``Any`` to support properties, as used by eg. ``whenever``.
            ''')]
    month: Annotated[
        int | Any,
        ClcNote('''Must be an int or int-like. Annotated to include
            ``Any`` to support properties, as used by eg. ``whenever``.
            ''')]
    day: Annotated[
        int | Any,
        ClcNote('''Must be an int or int-like. Annotated to include
            ``Any`` to support properties, as used by eg. ``whenever``.
            ''')]
