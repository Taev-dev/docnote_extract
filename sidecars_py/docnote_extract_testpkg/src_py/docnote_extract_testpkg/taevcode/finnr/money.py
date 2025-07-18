# This is a programmatically-vendored code sample
# that has been stubbified (ie, function bodies removed). Do not modify
# it directly; your changes will just be overwritten.

# The original source is:
# PkgSrcSpec(forge='github',
#            repo_id='Taev-dev/finnr',
#            pkg_name='finnr',
#            offset_dest_root_dir='taevcode',
#            root_path='src_py/finnr',
#            commit_hash='2a3cfc82a0ce3ab7fe3467e96d34238d87399745',
#            license_paths=set())

# The license of the original project is included in the top level of
# the vendored project directory.

# To regenerate, see sidecars/docnote_extract_testpkg_factory. The
# command is:
# ``uv run python -m docnote_extract_testpkg_factory``.

from __future__ import annotations
import operator
import typing
from dataclasses import dataclass
from decimal import ROUND_HALF_UP
from decimal import Decimal
from typing import Annotated
from docnote import ClcNote
import finnr._moneymath
from finnr._moneymath import MoneyMathImpl
if typing.TYPE_CHECKING:
    from finnr.currency import Currency
amount_getter: Annotated[
    operator.attrgetter[Decimal],
    ClcNote('''The ``amount_getter`` is a convenience method for use in
        ``min``, ``max``, sorting, etc. Use it instead of defining a lambda
        for every comparison:
        > ``amount_getter`` examples
        __embed__: 'code/python'
            max(money1, money2, key=amount_getter)
            sorted([money1, money2], key=amount_getter)
        ''')
] = operator.attrgetter('amount')
@dataclass(slots=True)
class Money(MoneyMathImpl):
    """Note that this might be theoretically nonsensical, for
    example, including fractional cents of the USD. This can be
    rounded either fractionally or decimally via the associated
    methods.
    """
    amount: Decimal
    currency: Currency
    def round_to_major(self, rounding=ROUND_HALF_UP) -> Money: ...
    def round_to_minor(self, rounding=ROUND_HALF_UP) -> Money: ...
    @property
    def is_nominal_division(self) -> bool: ...
    @property
    def is_nominal_major(self) -> bool: ...
finnr._moneymath.Money = Money
