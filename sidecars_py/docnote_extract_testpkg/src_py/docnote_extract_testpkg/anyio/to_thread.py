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
import sys
from collections.abc import Callable
from typing import TypeVar
from warnings import warn
from ._core._eventloop import get_async_backend
from .abc import CapacityLimiter
if sys.version_info >= (3, 11):
    from typing import TypeVarTuple, Unpack
else:
    from typing_extensions import TypeVarTuple, Unpack
T_Retval = TypeVar("T_Retval")
PosArgsT = TypeVarTuple("PosArgsT")
async def run_sync(
    func: Callable[[Unpack[PosArgsT]], T_Retval],
    *args: Unpack[PosArgsT],
    abandon_on_cancel: bool = False,
    cancellable: bool | None = None,
    limiter: CapacityLimiter | None = None,
) -> T_Retval:
    """
    Call the given function with the given arguments in a worker thread.
    If the ``cancellable`` option is enabled and the task waiting for its completion is
    cancelled, the thread will still run its course but its return value (or any raised
    exception) will be ignored.
    :param func: a callable
    :param args: positional arguments for the callable
    :param abandon_on_cancel: ``True`` to abandon the thread (leaving it to run
        unchecked on own) if the host task is cancelled, ``False`` to ignore
        cancellations in the host task until the operation has completed in the worker
        thread
    :param cancellable: deprecated alias of ``abandon_on_cancel``; will override
        ``abandon_on_cancel`` if both parameters are passed
    :param limiter: capacity limiter to use to limit the total amount of threads running
        (if omitted, the default limiter is used)
    :return: an awaitable that yields the return value of the function.
    """
    if cancellable is not None:
        abandon_on_cancel = cancellable
        warn(
            "The `cancellable=` keyword argument to `anyio.to_thread.run_sync` is "
            "deprecated since AnyIO 4.1.0; use `abandon_on_cancel=` instead",
            DeprecationWarning,
            stacklevel=2,
        )
    return await get_async_backend().run_sync_in_worker_thread(
        func, args, abandon_on_cancel=abandon_on_cancel, limiter=limiter
    )
def current_default_thread_limiter() -> CapacityLimiter:
    """
    Return the capacity limiter that is used by default to limit the number of
    concurrent threads.
    :return: a capacity limiter object
    """
    ...

