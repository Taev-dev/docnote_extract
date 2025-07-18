# This is a programmatically-vendored code sample
# that has been stubbified (ie, function bodies removed). Do not modify
# it directly; your changes will just be overwritten.

# The original source is:
# PkgSrcSpec(forge='github',
#            repo_id='agronholm/anyio',
#            pkg_name='anyio',
#            offset_dest_root_dir=None,
#            root_path='src/anyio',
#            commit_hash='65fe287039e2ded48752e1111a82c29d07725e36',
#            license_paths={'LICENSE'})

# The license of the original project is included in the top level of
# the vendored project directory.

# To regenerate, see sidecars/docnote_extract_testpkg_factory. The
# command is:
# ``uv run python -m docnote_extract_testpkg_factory``.

from __future__ import annotations
import atexit
import os
import pickle
import sys
from collections import deque
from collections.abc import Callable
from textwrap import dedent
from typing import Any, Final, TypeVar
from . import current_time, to_thread
from ._core._exceptions import BrokenWorkerInterpreter
from ._core._synchronization import CapacityLimiter
from .lowlevel import RunVar
if sys.version_info >= (3, 11):
    from typing import TypeVarTuple, Unpack
else:
    from typing_extensions import TypeVarTuple, Unpack
UNBOUND: Final = 2  
FMT_UNPICKLED: Final = 0
FMT_PICKLED: Final = 1
DEFAULT_CPU_COUNT: Final = 8  
MAX_WORKER_IDLE_TIME = (
    30  
)
QUEUE_PICKLE_ARGS: Final = (
    (UNBOUND,) if sys.version_info >= (3, 14, 0, "beta", 2) else (FMT_PICKLED, UNBOUND)
)
QUEUE_UNPICKLE_ARGS: Final = (
    (UNBOUND,)
    if sys.version_info >= (3, 14, 0, "beta", 2)
    else (FMT_UNPICKLED, UNBOUND)
)
T_Retval = TypeVar("T_Retval")
PosArgsT = TypeVarTuple("PosArgsT")
_idle_workers = RunVar[deque["Worker"]]("_available_workers")
_default_interpreter_limiter = RunVar[CapacityLimiter]("_default_interpreter_limiter")
class Worker:
    _run_func = compile(
        dedent("""
        import _interpqueues as queues
        import _interpreters as interpreters
        from pickle import loads, dumps, HIGHEST_PROTOCOL
        item = queues.get(queue_id)[0]
        try:
            func, args = loads(item)
            retval = func(*args)
        except BaseException as exc:
            is_exception = True
            retval = exc
        else:
            is_exception = False
        try:
            queues.put(queue_id, (retval, is_exception), *QUEUE_UNPICKLE_ARGS)
        except interpreters.NotShareableError:
            retval = dumps(retval, HIGHEST_PROTOCOL)
            queues.put(queue_id, (retval, is_exception), *QUEUE_PICKLE_ARGS)
        """),
        "<string>",
        "exec",
    )
    last_used: float = 0
    _initialized: bool = False
    _interpreter_id: int
    _queue_id: int
    def initialize(self) -> None:
        ...

    def destroy(self) -> None:
        ...

    def _call(
        self,
        func: Callable[..., T_Retval],
        args: tuple[Any],
    ) -> tuple[Any, bool]:
        ...

    async def call(
        self,
        func: Callable[..., T_Retval],
        args: tuple[Any],
        limiter: CapacityLimiter,
    ) -> T_Retval:
        result, is_exception = await to_thread.run_sync(
            self._call,
            func,
            args,
            limiter=limiter,
        )
        if is_exception:
            raise result
        return result
def _stop_workers(workers: deque[Worker]) -> None:
    ...

async def run_sync(
    func: Callable[[Unpack[PosArgsT]], T_Retval],
    *args: Unpack[PosArgsT],
    limiter: CapacityLimiter | None = None,
) -> T_Retval:
    """
    Call the given function with the given arguments in a subinterpreter.
    If the ``cancellable`` option is enabled and the task waiting for its completion is
    cancelled, the call will still run its course but its return value (or any raised
    exception) will be ignored.
    .. warning:: This feature is **experimental**. The upstream interpreter API has not
        yet been finalized or thoroughly tested, so don't rely on this for anything
        mission critical.
    :param func: a callable
    :param args: positional arguments for the callable
    :param limiter: capacity limiter to use to limit the total amount of subinterpreters
        running (if omitted, the default limiter is used)
    :return: the result of the call
    :raises BrokenWorkerInterpreter: if there's an internal error in a subinterpreter
    """
    if sys.version_info <= (3, 13):
        raise RuntimeError("subinterpreters require at least Python 3.13")
    if limiter is None:
        limiter = current_default_interpreter_limiter()
    try:
        idle_workers = _idle_workers.get()
    except LookupError:
        idle_workers = deque()
        _idle_workers.set(idle_workers)
        atexit.register(_stop_workers, idle_workers)
    async with limiter:
        try:
            worker = idle_workers.pop()
        except IndexError:
            worker = Worker()
    try:
        return await worker.call(func, args, limiter)
    finally:
        now = current_time()
        while idle_workers:
            if now - idle_workers[0].last_used <= MAX_WORKER_IDLE_TIME:
                break
            await to_thread.run_sync(idle_workers.popleft().destroy, limiter=limiter)
        worker.last_used = current_time()
        idle_workers.append(worker)
def current_default_interpreter_limiter() -> CapacityLimiter:
    """
    Return the capacity limiter that is used by default to limit the number of
    concurrently running subinterpreters.
    Defaults to the number of CPU cores.
    :return: a capacity limiter object
    """
    ...

