"""This is a programmatically-vendored code sample
that has been stubbified (ie, function bodies removed). Do not modify
it directly; your changes will just be overwritten.

The original source is:
PkgSrcSpec(forge='github',
           repo_id='agronholm/anyio',
           pkg_name='anyio',
           offset_dest_root_dir=None,
           root_path='src/anyio',
           commit_hash='65fe287039e2ded48752e1111a82c29d07725e36',
           license_paths={'LICENSE'})

The license of the original project is included in the top level of
the vendored project directory.

To regenerate, see sidecars/docnote_extract_testpkg_factory. The
command is:
``uv run python -m docnote_extract_testpkg_factory``.

"""
from __future__ import annotations
import enum
from dataclasses import dataclass
from typing import Any, Generic, Literal, TypeVar, overload
from weakref import WeakKeyDictionary
from ._core._eventloop import get_async_backend
T = TypeVar("T")
D = TypeVar("D")
async def checkpoint() -> None:
    """
    Check for cancellation and allow the scheduler to switch to another task.
    Equivalent to (but more efficient than)::
        await checkpoint_if_cancelled()
        await cancel_shielded_checkpoint()
    .. versionadded:: 3.0
    """
    await get_async_backend().checkpoint()
async def checkpoint_if_cancelled() -> None:
    """
    Enter a checkpoint if the enclosing cancel scope has been cancelled.
    This does not allow the scheduler to switch to a different task.
    .. versionadded:: 3.0
    """
    await get_async_backend().checkpoint_if_cancelled()
async def cancel_shielded_checkpoint() -> None:
    """
    Allow the scheduler to switch to another task but without checking for cancellation.
    Equivalent to (but potentially more efficient than)::
        with CancelScope(shield=True):
            await checkpoint()
    .. versionadded:: 3.0
    """
    await get_async_backend().cancel_shielded_checkpoint()
def current_token() -> object:
    """
    Return a backend specific token object that can be used to get back to the event
    loop.
    """
    ...

_run_vars: WeakKeyDictionary[Any, dict[RunVar[Any], Any]] = WeakKeyDictionary()
_token_wrappers: dict[Any, _TokenWrapper] = {}
@dataclass(frozen=True)
class _TokenWrapper:
    __slots__ = "_token", "__weakref__"
    _token: object
class _NoValueSet(enum.Enum):
    NO_VALUE_SET = enum.auto()
class RunvarToken(Generic[T]):
    __slots__ = "_var", "_value", "_redeemed"
    def __init__(self, var: RunVar[T], value: T | Literal[_NoValueSet.NO_VALUE_SET]):
        ...

class RunVar(Generic[T]):
    """
    Like a :class:`~contextvars.ContextVar`, except scoped to the running event loop.
    """
    __slots__ = "_name", "_default"
    NO_VALUE_SET: Literal[_NoValueSet.NO_VALUE_SET] = _NoValueSet.NO_VALUE_SET
    _token_wrappers: set[_TokenWrapper] = set()
    def __init__(
        self, name: str, default: T | Literal[_NoValueSet.NO_VALUE_SET] = NO_VALUE_SET
    ):
        ...

    @property
    def _current_vars(self) -> dict[RunVar[T], T]:
        ...

    @overload
    def get(self, default: D) -> T | D: ...
    @overload
    def get(self) -> T: ...
    def get(
        self, default: D | Literal[_NoValueSet.NO_VALUE_SET] = NO_VALUE_SET
    ) -> T | D:
        ...

    def set(self, value: T) -> RunvarToken[T]:
        ...

    def reset(self, token: RunvarToken[T]) -> None:
        ...

    def __repr__(self) -> str:
        ...

