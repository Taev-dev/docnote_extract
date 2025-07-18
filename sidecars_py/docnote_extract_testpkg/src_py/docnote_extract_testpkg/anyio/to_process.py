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
import os
import pickle
import subprocess
import sys
from collections import deque
from collections.abc import Callable
from importlib.util import module_from_spec, spec_from_file_location
from typing import TypeVar, cast
from ._core._eventloop import current_time, get_async_backend, get_cancelled_exc_class
from ._core._exceptions import BrokenWorkerProcess
from ._core._subprocesses import open_process
from ._core._synchronization import CapacityLimiter
from ._core._tasks import CancelScope, fail_after
from .abc import ByteReceiveStream, ByteSendStream, Process
from .lowlevel import RunVar, checkpoint_if_cancelled
from .streams.buffered import BufferedByteReceiveStream
if sys.version_info >= (3, 11):
    from typing import TypeVarTuple, Unpack
else:
    from typing_extensions import TypeVarTuple, Unpack
WORKER_MAX_IDLE_TIME = 300  
T_Retval = TypeVar("T_Retval")
PosArgsT = TypeVarTuple("PosArgsT")
_process_pool_workers: RunVar[set[Process]] = RunVar("_process_pool_workers")
_process_pool_idle_workers: RunVar[deque[tuple[Process, float]]] = RunVar(
    "_process_pool_idle_workers"
)
_default_process_limiter: RunVar[CapacityLimiter] = RunVar("_default_process_limiter")
async def run_sync(  
    func: Callable[[Unpack[PosArgsT]], T_Retval],
    *args: Unpack[PosArgsT],
    cancellable: bool = False,
    limiter: CapacityLimiter | None = None,
) -> T_Retval:
    """
    Call the given function with the given arguments in a worker process.
    If the ``cancellable`` option is enabled and the task waiting for its completion is
    cancelled, the worker process running it will be abruptly terminated using SIGKILL
    (or ``terminateProcess()`` on Windows).
    :param func: a callable
    :param args: positional arguments for the callable
    :param cancellable: ``True`` to allow cancellation of the operation while it's
        running
    :param limiter: capacity limiter to use to limit the total amount of processes
        running (if omitted, the default limiter is used)
    :return: an awaitable that yields the return value of the function.
    """
    async def send_raw_command(pickled_cmd: bytes) -> object:
        try:
            await stdin.send(pickled_cmd)
            response = await buffered.receive_until(b"\n", 50)
            status, length = response.split(b" ")
            if status not in (b"RETURN", b"EXCEPTION"):
                raise RuntimeError(
                    f"Worker process returned unexpected response: {response!r}"
                )
            pickled_response = await buffered.receive_exactly(int(length))
        except BaseException as exc:
            workers.discard(process)
            try:
                process.kill()
                with CancelScope(shield=True):
                    await process.aclose()
            except ProcessLookupError:
                pass
            if isinstance(exc, get_cancelled_exc_class()):
                raise
            else:
                raise BrokenWorkerProcess from exc
        retval = pickle.loads(pickled_response)
        if status == b"EXCEPTION":
            assert isinstance(retval, BaseException)
            raise retval
        else:
            return retval
    await checkpoint_if_cancelled()
    request = pickle.dumps(("run", func, args), protocol=pickle.HIGHEST_PROTOCOL)
    try:
        workers = _process_pool_workers.get()
        idle_workers = _process_pool_idle_workers.get()
    except LookupError:
        workers = set()
        idle_workers = deque()
        _process_pool_workers.set(workers)
        _process_pool_idle_workers.set(idle_workers)
        get_async_backend().setup_process_pool_exit_at_shutdown(workers)
    async with limiter or current_default_process_limiter():
        process: Process
        while idle_workers:
            process, idle_since = idle_workers.pop()
            if process.returncode is None:
                stdin = cast(ByteSendStream, process.stdin)
                buffered = BufferedByteReceiveStream(
                    cast(ByteReceiveStream, process.stdout)
                )
                now = current_time()
                killed_processes: list[Process] = []
                while idle_workers:
                    if now - idle_workers[0][1] < WORKER_MAX_IDLE_TIME:
                        break
                    process_to_kill, idle_since = idle_workers.popleft()
                    process_to_kill.kill()
                    workers.remove(process_to_kill)
                    killed_processes.append(process_to_kill)
                with CancelScope(shield=True):
                    for killed_process in killed_processes:
                        await killed_process.aclose()
                break
            workers.remove(process)
        else:
            command = [sys.executable, "-u", "-m", __name__]
            process = await open_process(
                command, stdin=subprocess.PIPE, stdout=subprocess.PIPE
            )
            try:
                stdin = cast(ByteSendStream, process.stdin)
                buffered = BufferedByteReceiveStream(
                    cast(ByteReceiveStream, process.stdout)
                )
                with fail_after(20):
                    message = await buffered.receive(6)
                if message != b"READY\n":
                    raise BrokenWorkerProcess(
                        f"Worker process returned unexpected response: {message!r}"
                    )
                main_module_path = getattr(sys.modules["__main__"], "__file__", None)
                pickled = pickle.dumps(
                    ("init", sys.path, main_module_path),
                    protocol=pickle.HIGHEST_PROTOCOL,
                )
                await send_raw_command(pickled)
            except (BrokenWorkerProcess, get_cancelled_exc_class()):
                raise
            except BaseException as exc:
                process.kill()
                raise BrokenWorkerProcess(
                    "Error during worker process initialization"
                ) from exc
            workers.add(process)
        with CancelScope(shield=not cancellable):
            try:
                return cast(T_Retval, await send_raw_command(request))
            finally:
                if process in workers:
                    idle_workers.append((process, current_time()))
def current_default_process_limiter() -> CapacityLimiter:
    """
    Return the capacity limiter that is used by default to limit the number of worker
    processes.
    :return: a capacity limiter object
    """
    ...

def process_worker() -> None:
    ...

if __name__ == "__main__":
    process_worker()
