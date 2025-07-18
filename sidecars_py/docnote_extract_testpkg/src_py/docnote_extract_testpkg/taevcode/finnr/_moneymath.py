"""This is a programmatically-vendored code sample
that has been stubbified (ie, function bodies removed). Do not modify
it directly; your changes will just be overwritten.

The original source is:
PkgSrcSpec(forge='github',
           repo_id='Taev-dev/finnr',
           pkg_name='finnr',
           offset_dest_root_dir='taevcode',
           root_path='src_py/finnr',
           commit_hash='2a3cfc82a0ce3ab7fe3467e96d34238d87399745',
           license_paths=set())

The license of the original project is included in the top level of
the vendored project directory.

To regenerate, see sidecars/docnote_extract_testpkg_factory. The
command is:
``uv run python -m docnote_extract_testpkg_factory``.

"""
"""THIS MODULE IS 100% AUTOMATICALLY GENERATED VIA THE CODEGEN SIDECAR
(See sidecars_py).
Do not modify it directly.
Some notes:
++  We want to strictly separate the codegen from any custom
    implementation as part of the ``Money`` object, so this module
    contains ONLY money math.
++  The circular injection of ``Money`` is simply the most performant
    way to access the Money object.
++  Note that decimal doesn't implement augmented operations; therefore,
    we have to be careful to reference the non-augmented methods within
    the template
++  There are some things that are marked as overloads that could have
    been converted into a separate template for unions, since they
    aren't actually overloads (eg ``__mod__``), but rather,
    ``other: _Scalar | Money -> Money``. These used to be actual
    overloads, but I changed them when I realized they didn't make any
    sense like that. Might be worth cleaning them up later, but for now,
    it's not hurting anything.
"""
from __future__ import annotations
import typing
from decimal import Context
from decimal import Decimal
from typing import Protocol
from typing import Self
from typing import overload
from finnr.exceptions import MismatchedCurrency
from finnr.exceptions import MoneyRequired
from finnr.exceptions import ScalarRequired
if typing.TYPE_CHECKING:
    from finnr.currency import Currency
    from finnr.money import Money
type _Scalar = Decimal | int
class MoneyMathImpl(Protocol):
    amount: Decimal
    currency: Currency
    def __init__(self, amount: Decimal, currency: Currency): ...
    def __mul__(self, other: _Scalar) -> Money:
        ...

    def __rmul__(self, other: _Scalar) -> Money:
        ...

    def __add__(self, other: Money) -> Money:
        ...

    def __sub__(self, other: Money) -> Money:
        ...

    def __imul__(self, other: _Scalar) -> Self:
        ...

    def __iadd__(self, other: Money) -> Self:
        ...

    def __isub__(self, other: Money) -> Self:
        ...

    @overload
    def __truediv__(self, other: Money) -> Decimal: ...
    @overload
    def __truediv__(self, other: _Scalar) -> Money: ...
    def __truediv__(self, other: Money | _Scalar) -> Money | Decimal:
        ...

    @overload
    def __floordiv__(self, other: Money) -> Decimal: ...
    @overload
    def __floordiv__(self, other: _Scalar) -> Money: ...
    def __floordiv__(self, other: Money | _Scalar) -> Money | Decimal:
        ...

    @overload
    def __mod__(self, other: Money) -> Money: ...
    @overload
    def __mod__(self, other: _Scalar) -> Money: ...
    def __mod__(self, other: Money | _Scalar) -> Money:
        ...

    def __itruediv__(self, other: _Scalar) -> Self:
        ...

    def __ifloordiv__(self, other: _Scalar) -> Self:
        ...

    def __imod__(self, other: _Scalar) -> Self:
        ...

    def __round__(self) -> Money:
        ...

    def __trunc__(self) -> Money:
        ...

    def __floor__(self) -> Money:
        ...

    def __ceil__(self) -> Money:
        ...

    def __int__(self) -> int:
        ...

    def __float__(self) -> float:
        ...

    def __neg__(self) -> Money:
        ...

    def __pos__(self) -> Money:
        ...

    def __abs__(self) -> Money:
        ...

    def compare(
            self,
            other: Money,
            context: Context | None = None
            ) -> _Scalar:
        ...

    def compare_signal(
            self,
            other: Money,
            context: Context | None = None
            ) -> _Scalar:
        ...

    def compare_total(
            self,
            other: Money,
            context: Context | None = None
            ) -> _Scalar:
        ...

    def compare_total_mag(
            self,
            other: Money,
            context: Context | None = None
            ) -> _Scalar:
        ...

    @overload
    def remainder_near(
            self,
            other: Money,
            context: Context | None = None
            ) -> Money: ...
    @overload
    def remainder_near(
            self,
            other: _Scalar,
            context: Context | None = None
            ) -> Money: ...
    def remainder_near(
            self,
            other: Money | _Scalar,
            context: Context | None = None
            ) -> Money:
        ...

    def shift(
            self,
            other: _Scalar,
            context: Context | None = None
            ) -> Money:
        ...

    def scaleb(
            self,
            other: _Scalar,
            context: Context | None = None
            ) -> Money:
        ...

    def rotate(
            self,
            other: _Scalar,
            context: Context | None = None
            ) -> Money:
        ...

    def same_quantum(
            self,
            other: Money,
            context: Context | None = None
            ) -> bool:
        ...

    def next_minus(self, context: Context | None = None) -> Money:
        ...

    def next_plus(self, context: Context | None = None) -> Money:
        ...

    def normalize(self, context: Context | None = None) -> Money:
        ...

    def is_finite(self) -> bool:
        ...

    def is_infinite(self) -> bool:
        ...

    def is_nan(self) -> bool:
        ...

    def is_qnan(self) -> bool:
        ...

    def is_signed(self) -> bool:
        ...

    def is_snan(self) -> bool:
        ...

    def is_zero(self) -> bool:
        ...

    def next_toward(
            self,
            other: Money,
            context: Context | None = None
            ) -> Money:
        ...

    def max(
            self,
            other: Money,
            context: Context | None = None
            ) -> Money:
        ...

    def max_mag(
            self,
            other: Money,
            context: Context | None = None
            ) -> Money:
        ...

    def min(
            self,
            other: Money,
            context: Context | None = None
            ) -> Money:
        ...

    def min_mag(
            self,
            other: Money,
            context: Context | None = None
            ) -> Money:
        ...

    def copy_sign(
            self,
            other: Money,
            context: Context | None = None
            ) -> Money:
        ...

    @overload
    def __divmod__(self, other: Money) -> tuple[Decimal, Money]: ...
    @overload
    def __divmod__(self, other: Decimal | int) -> tuple[Money, Money]: ...
    def __divmod__(
            self,
            other: Decimal | int | Money
            ) -> tuple[Decimal | Money, Money]:
        ...

    def adjusted(self) -> int:
        ...

    def fma(
            self,
            other: Decimal | int,
            third: Money,
            context=None
            ) -> Money:
        ...

    def quantize(
            self,
            exp: Decimal | int | Money,
            rounding: str | None = None,
            context: Context | None = None,
            ) -> Money:
        ...

