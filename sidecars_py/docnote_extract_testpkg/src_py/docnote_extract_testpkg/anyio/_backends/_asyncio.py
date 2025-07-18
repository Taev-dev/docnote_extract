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
import array
import asyncio
import concurrent.futures
import contextvars
import math
import os
import socket
import sys
import threading
import weakref
from asyncio import (
    AbstractEventLoop,
    CancelledError,
    all_tasks,
    create_task,
    current_task,
    get_running_loop,
    sleep,
)
from asyncio.base_events import _run_until_complete_cb  
from collections import OrderedDict, deque
from collections.abc import (
    AsyncGenerator,
    AsyncIterator,
    Awaitable,
    Callable,
    Collection,
    Coroutine,
    Iterable,
    Sequence,
)
from concurrent.futures import Future
from contextlib import AbstractContextManager, suppress
from contextvars import Context, copy_context
from dataclasses import dataclass
from functools import partial, wraps
from inspect import (
    CORO_RUNNING,
    CORO_SUSPENDED,
    getcoroutinestate,
    iscoroutine,
)
from io import IOBase
from os import PathLike
from queue import Queue
from signal import Signals
from socket import AddressFamily, SocketKind
from threading import Thread
from types import CodeType, TracebackType
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    Optional,
    TypeVar,
    cast,
)
from weakref import WeakKeyDictionary
import sniffio
from .. import (
    CapacityLimiterStatistics,
    EventStatistics,
    LockStatistics,
    TaskInfo,
    abc,
)
from .._core._eventloop import claim_worker_thread, threadlocals
from .._core._exceptions import (
    BrokenResourceError,
    BusyResourceError,
    ClosedResourceError,
    EndOfStream,
    WouldBlock,
    iterate_exceptions,
)
from .._core._sockets import convert_ipv6_sockaddr
from .._core._streams import create_memory_object_stream
from .._core._synchronization import (
    CapacityLimiter as BaseCapacityLimiter,
)
from .._core._synchronization import Event as BaseEvent
from .._core._synchronization import Lock as BaseLock
from .._core._synchronization import (
    ResourceGuard,
    SemaphoreStatistics,
)
from .._core._synchronization import Semaphore as BaseSemaphore
from .._core._tasks import CancelScope as BaseCancelScope
from ..abc import (
    AsyncBackend,
    IPSockAddrType,
    SocketListener,
    UDPPacketType,
    UNIXDatagramPacketType,
)
from ..abc._eventloop import StrOrBytesPath
from ..lowlevel import RunVar
from ..streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
if TYPE_CHECKING:
    from _typeshed import FileDescriptorLike
else:
    FileDescriptorLike = object
if sys.version_info >= (3, 10):
    from typing import ParamSpec
else:
    from typing_extensions import ParamSpec
if sys.version_info >= (3, 11):
    from asyncio import Runner
    from typing import TypeVarTuple, Unpack
else:
    import contextvars
    import enum
    import signal
    from asyncio import coroutines, events, exceptions, tasks
    from exceptiongroup import BaseExceptionGroup
    from typing_extensions import TypeVarTuple, Unpack
    class _State(enum.Enum):
        CREATED = "created"
        INITIALIZED = "initialized"
        CLOSED = "closed"
    class Runner:
        
        def __init__(
            self,
            *,
            debug: bool | None = None,
            loop_factory: Callable[[], AbstractEventLoop] | None = None,
        ):
            ...

        def __enter__(self) -> Runner:
            ...

        def __exit__(
            self,
            exc_type: type[BaseException],
            exc_val: BaseException,
            exc_tb: TracebackType,
        ) -> None:
            ...

        def close(self) -> None:
            """Shutdown and close event loop."""
            if self._state is not _State.INITIALIZED:
                return
            try:
                loop = self._loop
                _cancel_all_tasks(loop)
                loop.run_until_complete(loop.shutdown_asyncgens())
                if hasattr(loop, "shutdown_default_executor"):
                    loop.run_until_complete(loop.shutdown_default_executor())
                else:
                    loop.run_until_complete(_shutdown_default_executor(loop))
            finally:
                if self._set_event_loop:
                    events.set_event_loop(None)
                loop.close()
                self._loop = None
                self._state = _State.CLOSED
        def get_loop(self) -> AbstractEventLoop:
            """Return embedded event loop."""
            ...

        def run(self, coro: Coroutine[T_Retval], *, context=None) -> T_Retval:
            """Run a coroutine inside the embedded event loop."""
            if not coroutines.iscoroutine(coro):
                raise ValueError(f"a coroutine was expected, got {coro!r}")
            if events._get_running_loop() is not None:
                raise RuntimeError(
                    "Runner.run() cannot be called from a running event loop"
                )
            self._lazy_init()
            if context is None:
                context = self._context
            task = context.run(self._loop.create_task, coro)
            if (
                threading.current_thread() is threading.main_thread()
                and signal.getsignal(signal.SIGINT) is signal.default_int_handler
            ):
                sigint_handler = partial(self._on_sigint, main_task=task)
                try:
                    signal.signal(signal.SIGINT, sigint_handler)
                except ValueError:
                    sigint_handler = None
            else:
                sigint_handler = None
            self._interrupt_count = 0
            try:
                return self._loop.run_until_complete(task)
            except exceptions.CancelledError:
                if self._interrupt_count > 0:
                    uncancel = getattr(task, "uncancel", None)
                    if uncancel is not None and uncancel() == 0:
                        raise KeyboardInterrupt  
                raise  
            finally:
                if (
                    sigint_handler is not None
                    and signal.getsignal(signal.SIGINT) is sigint_handler
                ):
                    signal.signal(signal.SIGINT, signal.default_int_handler)
        def _lazy_init(self) -> None:
            if self._state is _State.CLOSED:
                raise RuntimeError("Runner is closed")
            if self._state is _State.INITIALIZED:
                return
            if self._loop_factory is None:
                self._loop = events.new_event_loop()
                if not self._set_event_loop:
                    events.set_event_loop(self._loop)
                    self._set_event_loop = True
            else:
                self._loop = self._loop_factory()
            if self._debug is not None:
                self._loop.set_debug(self._debug)
            self._context = contextvars.copy_context()
            self._state = _State.INITIALIZED
        def _on_sigint(self, signum, frame, main_task: asyncio.Task) -> None:
            self._interrupt_count += 1
            if self._interrupt_count == 1 and not main_task.done():
                main_task.cancel()
                self._loop.call_soon_threadsafe(lambda: None)
                return
            raise KeyboardInterrupt()
    def _cancel_all_tasks(loop: AbstractEventLoop) -> None:
        to_cancel = tasks.all_tasks(loop)
        if not to_cancel:
            return
        for task in to_cancel:
            task.cancel()
        loop.run_until_complete(tasks.gather(*to_cancel, return_exceptions=True))
        for task in to_cancel:
            if task.cancelled():
                continue
            if task.exception() is not None:
                loop.call_exception_handler(
                    {
                        "message": "unhandled exception during asyncio.run() shutdown",
                        "exception": task.exception(),
                        "task": task,
                    }
                )
    async def _shutdown_default_executor(loop: AbstractEventLoop) -> None:
        """Schedule the shutdown of the default executor."""
            ...

        def _do_shutdown(future: asyncio.futures.Future) -> None:
            ...

        loop._executor_shutdown_called = True
        if loop._default_executor is None:
            return
        future = loop.create_future()
        thread = threading.Thread(target=_do_shutdown, args=(future,))
        thread.start()
        try:
            await future
        finally:
            thread.join()
T_Retval = TypeVar("T_Retval")
T_contra = TypeVar("T_contra", contravariant=True)
PosArgsT = TypeVarTuple("PosArgsT")
P = ParamSpec("P")
_root_task: RunVar[asyncio.Task | None] = RunVar("_root_task")
def find_root_task() -> asyncio.Task:
    ...

def get_callable_name(func: Callable) -> str:
    ...

_run_vars: WeakKeyDictionary[asyncio.AbstractEventLoop, Any] = WeakKeyDictionary()
def _task_started(task: asyncio.Task) -> bool:
    """Return ``True`` if the task has been started and has not finished."""
    coro = task.get_coro()
    assert coro is not None
    try:
        return getcoroutinestate(coro) in (CORO_RUNNING, CORO_SUSPENDED)
    except AttributeError:
        raise Exception(f"Cannot determine if task {task} has started or not") from None
def is_anyio_cancellation(exc: CancelledError) -> bool:
    while True:
        if (
            exc.args
            and isinstance(exc.args[0], str)
            and exc.args[0].startswith("Cancelled by cancel scope ")
        ):
            return True
        if isinstance(exc.__context__, CancelledError):
            exc = exc.__context__
            continue
        return False
class CancelScope(BaseCancelScope):
    def __new__(
        cls, *, deadline: float = math.inf, shield: bool = False
    ) -> CancelScope:
        return object.__new__(cls)
    def __init__(self, deadline: float = math.inf, shield: bool = False):
        self._deadline = deadline
        self._shield = shield
        self._parent_scope: CancelScope | None = None
        self._child_scopes: set[CancelScope] = set()
        self._cancel_called = False
        self._cancelled_caught = False
        self._active = False
        self._timeout_handle: asyncio.TimerHandle | None = None
        self._cancel_handle: asyncio.Handle | None = None
        self._tasks: set[asyncio.Task] = set()
        self._host_task: asyncio.Task | None = None
        if sys.version_info >= (3, 11):
            self._pending_uncancellations: int | None = 0
        else:
            self._pending_uncancellations = None
    def __enter__(self) -> CancelScope:
        if self._active:
            raise RuntimeError(
                "Each CancelScope may only be used for a single 'with' block"
            )
        self._host_task = host_task = cast(asyncio.Task, current_task())
        self._tasks.add(host_task)
        try:
            task_state = _task_states[host_task]
        except KeyError:
            task_state = TaskState(None, self)
            _task_states[host_task] = task_state
        else:
            self._parent_scope = task_state.cancel_scope
            task_state.cancel_scope = self
            if self._parent_scope is not None:
                self._parent_scope._child_scopes.add(self)
                self._parent_scope._tasks.discard(host_task)
        self._timeout()
        self._active = True
        if self._cancel_called:
            self._deliver_cancellation(self)
        return self
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        del exc_tb
        if not self._active:
            raise RuntimeError("This cancel scope is not active")
        if current_task() is not self._host_task:
            raise RuntimeError(
                "Attempted to exit cancel scope in a different task than it was "
                "entered in"
            )
        assert self._host_task is not None
        host_task_state = _task_states.get(self._host_task)
        if host_task_state is None or host_task_state.cancel_scope is not self:
            raise RuntimeError(
                "Attempted to exit a cancel scope that isn't the current tasks's "
                "current cancel scope"
            )
        try:
            self._active = False
            if self._timeout_handle:
                self._timeout_handle.cancel()
                self._timeout_handle = None
            self._tasks.remove(self._host_task)
            if self._parent_scope is not None:
                self._parent_scope._child_scopes.remove(self)
                self._parent_scope._tasks.add(self._host_task)
            host_task_state.cancel_scope = self._parent_scope
            self._restart_cancellation_in_parent()
            if self._cancel_called and not self._parent_cancellation_is_visible_to_us:
                while self._pending_uncancellations:
                    self._host_task.uncancel()
                    self._pending_uncancellations -= 1
                cannot_swallow_exc_val = False
                if exc_val is not None:
                    for exc in iterate_exceptions(exc_val):
                        if isinstance(exc, CancelledError) and is_anyio_cancellation(
                            exc
                        ):
                            self._cancelled_caught = True
                        else:
                            cannot_swallow_exc_val = True
                return self._cancelled_caught and not cannot_swallow_exc_val
            else:
                if self._pending_uncancellations:
                    assert self._parent_scope is not None
                    assert self._parent_scope._pending_uncancellations is not None
                    self._parent_scope._pending_uncancellations += (
                        self._pending_uncancellations
                    )
                    self._pending_uncancellations = 0
                return False
        finally:
            self._host_task = None
            del exc_val
    @property
    def _effectively_cancelled(self) -> bool:
        cancel_scope: CancelScope | None = self
        while cancel_scope is not None:
            if cancel_scope._cancel_called:
                return True
            if cancel_scope.shield:
                return False
            cancel_scope = cancel_scope._parent_scope
        return False
    @property
    def _parent_cancellation_is_visible_to_us(self) -> bool:
        return (
            self._parent_scope is not None
            and not self.shield
            and self._parent_scope._effectively_cancelled
        )
    def _timeout(self) -> None:
        if self._deadline != math.inf:
            loop = get_running_loop()
            if loop.time() >= self._deadline:
                self.cancel()
            else:
                self._timeout_handle = loop.call_at(self._deadline, self._timeout)
    def _deliver_cancellation(self, origin: CancelScope) -> bool:
        """
    ...

class TaskState:
    """
    Encapsulates auxiliary task information that cannot be added to the Task instance
    itself because there are no guarantees about its implementation.
    """
    __slots__ = "parent_id", "cancel_scope", "__weakref__"
    def __init__(self, parent_id: int | None, cancel_scope: CancelScope | None):
        ...

_task_states: WeakKeyDictionary[asyncio.Task, TaskState] = WeakKeyDictionary()
class _AsyncioTaskStatus(abc.TaskStatus):
    def __init__(self, future: asyncio.Future, parent_id: int):
        ...

    def started(self, value: T_contra | None = None) -> None:
        ...

if sys.version_info >= (3, 12):
    _eager_task_factory_code: CodeType | None = asyncio.eager_task_factory.__code__
else:
    _eager_task_factory_code = None
class TaskGroup(abc.TaskGroup):
    def __init__(self) -> None:
        ...

    async def __aenter__(self) -> TaskGroup:
        self.cancel_scope.__enter__()
        self._active = True
        return self
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        try:
            if exc_val is not None:
                self.cancel_scope.cancel()
                if not isinstance(exc_val, CancelledError):
                    self._exceptions.append(exc_val)
            loop = get_running_loop()
            try:
                if self._tasks:
                    with CancelScope() as wait_scope:
                        while self._tasks:
                            self._on_completed_fut = loop.create_future()
                            try:
                                await self._on_completed_fut
                            except CancelledError as exc:
                                
                                
                                wait_scope.shield = True
                                self.cancel_scope.cancel()
                                
                                
                                
                                if exc_val is None or (
                                    isinstance(exc_val, CancelledError)
                                    and not is_anyio_cancellation(exc)
                                ):
                                    exc_val = exc
                            self._on_completed_fut = None
                else:
                    
                    
                    await AsyncIOBackend.cancel_shielded_checkpoint()
                self._active = False
                if self._exceptions:
                    
                    
                    
                    
                    raise BaseExceptionGroup(
                        "unhandled errors in a TaskGroup", self._exceptions
                    ) from None
                elif exc_val:
                    raise exc_val
            except BaseException as exc:
                if self.cancel_scope.__exit__(type(exc), exc, exc.__traceback__):
                    return True
                raise
            return self.cancel_scope.__exit__(exc_type, exc_val, exc_tb)
        finally:
            del exc_val, exc_tb, self._exceptions
    def _spawn(
        self,
        func: Callable[[Unpack[PosArgsT]], Awaitable[Any]],
        args: tuple[Unpack[PosArgsT]],
        name: object,
        task_status_future: asyncio.Future | None = None,
    ) -> asyncio.Task:
        ...

    def start_soon(
        self,
        func: Callable[[Unpack[PosArgsT]], Awaitable[Any]],
        *args: Unpack[PosArgsT],
        name: object = None,
    ) -> None:
        ...

    async def start(
        self, func: Callable[..., Awaitable[Any]], *args: object, name: object = None
    ) -> Any:
        future: asyncio.Future = asyncio.Future()
        task = self._spawn(func, args, name, future)
        
        
        
        
        try:
            return await future
        except CancelledError:
            
            task.cancel()
            with CancelScope(shield=True), suppress(CancelledError):
                await task
            raise
_Retval_Queue_Type = tuple[Optional[T_Retval], Optional[BaseException]]
class WorkerThread(Thread):
    MAX_IDLE_TIME = 10  
    def __init__(
        self,
        root_task: asyncio.Task,
        workers: set[WorkerThread],
        idle_workers: deque[WorkerThread],
    ):
        ...

    def _report_result(
        self, future: asyncio.Future, result: Any, exc: BaseException | None
    ) -> None:
        ...

    def run(self) -> None:
        ...

    def stop(self, f: asyncio.Task | None = None) -> None:
        ...

_threadpool_idle_workers: RunVar[deque[WorkerThread]] = RunVar(
    "_threadpool_idle_workers"
)
_threadpool_workers: RunVar[set[WorkerThread]] = RunVar("_threadpool_workers")
class BlockingPortal(abc.BlockingPortal):
    def __new__(cls) -> BlockingPortal:
        ...

    def __init__(self) -> None:
        ...

    def _spawn_task_from_thread(
        self,
        func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval] | T_Retval],
        args: tuple[Unpack[PosArgsT]],
        kwargs: dict[str, Any],
        name: object,
        future: Future[T_Retval],
    ) -> None:
        ...

@dataclass(eq=False)
class StreamReaderWrapper(abc.ByteReceiveStream):
    _stream: asyncio.StreamReader
    async def receive(self, max_bytes: int = 65536) -> bytes:
        data = await self._stream.read(max_bytes)
        if data:
            return data
        else:
            raise EndOfStream
    async def aclose(self) -> None:
        self._stream.set_exception(ClosedResourceError())
        await AsyncIOBackend.checkpoint()
@dataclass(eq=False)
class StreamWriterWrapper(abc.ByteSendStream):
    _stream: asyncio.StreamWriter
    async def send(self, item: bytes) -> None:
        self._stream.write(item)
        await self._stream.drain()
    async def aclose(self) -> None:
        self._stream.close()
        await AsyncIOBackend.checkpoint()
@dataclass(eq=False)
class Process(abc.Process):
    _process: asyncio.subprocess.Process
    _stdin: StreamWriterWrapper | None
    _stdout: StreamReaderWrapper | None
    _stderr: StreamReaderWrapper | None
    async def aclose(self) -> None:
        with CancelScope(shield=True) as scope:
            if self._stdin:
                await self._stdin.aclose()
            if self._stdout:
                await self._stdout.aclose()
            if self._stderr:
                await self._stderr.aclose()
            scope.shield = False
            try:
                await self.wait()
            except BaseException:
                scope.shield = True
                self.kill()
                await self.wait()
                raise
    async def wait(self) -> int:
        return await self._process.wait()
    def terminate(self) -> None:
        ...

    def kill(self) -> None:
        ...

    def send_signal(self, signal: int) -> None:
        ...

    @property
    def pid(self) -> int:
        ...

    @property
    def returncode(self) -> int | None:
        ...

    @property
    def stdin(self) -> abc.ByteSendStream | None:
        ...

    @property
    def stdout(self) -> abc.ByteReceiveStream | None:
        ...

    @property
    def stderr(self) -> abc.ByteReceiveStream | None:
        ...

def _forcibly_shutdown_process_pool_on_exit(
    workers: set[Process], _task: object
) -> None:
    """
    Forcibly shuts down worker processes belonging to this event loop."""
    ...

async def _shutdown_process_pool_on_exit(workers: set[abc.Process]) -> None:
    """
    Shuts down worker processes belonging to this event loop.
    NOTE: this only works when the event loop was started using asyncio.run() or
    anyio.run().
    """
    process: abc.Process
    try:
        await sleep(math.inf)
    except asyncio.CancelledError:
        for process in workers:
            if process.returncode is None:
                process.kill()
        for process in workers:
            await process.aclose()
class StreamProtocol(asyncio.Protocol):
    read_queue: deque[bytes]
    read_event: asyncio.Event
    write_event: asyncio.Event
    exception: Exception | None = None
    is_at_eof: bool = False
    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        ...

    def connection_lost(self, exc: Exception | None) -> None:
        ...

    def data_received(self, data: bytes) -> None:
        ...

    def eof_received(self) -> bool | None:
        ...

    def pause_writing(self) -> None:
        ...

    def resume_writing(self) -> None:
        ...

class DatagramProtocol(asyncio.DatagramProtocol):
    read_queue: deque[tuple[bytes, IPSockAddrType]]
    read_event: asyncio.Event
    write_event: asyncio.Event
    exception: Exception | None = None
    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        ...

    def connection_lost(self, exc: Exception | None) -> None:
        ...

    def datagram_received(self, data: bytes, addr: IPSockAddrType) -> None:
        ...

    def error_received(self, exc: Exception) -> None:
        ...

    def pause_writing(self) -> None:
        ...

    def resume_writing(self) -> None:
        ...

class SocketStream(abc.SocketStream):
    def __init__(self, transport: asyncio.Transport, protocol: StreamProtocol):
        ...

    @property
    def _raw_socket(self) -> socket.socket:
        ...

    async def receive(self, max_bytes: int = 65536) -> bytes:
        with self._receive_guard:
            if (
                not self._protocol.read_event.is_set()
                and not self._transport.is_closing()
                and not self._protocol.is_at_eof
            ):
                self._transport.resume_reading()
                await self._protocol.read_event.wait()
                self._transport.pause_reading()
            else:
                await AsyncIOBackend.checkpoint()
            try:
                chunk = self._protocol.read_queue.popleft()
            except IndexError:
                if self._closed:
                    raise ClosedResourceError from None
                elif self._protocol.exception:
                    raise self._protocol.exception from None
                else:
                    raise EndOfStream from None
            if len(chunk) > max_bytes:
                
                chunk, leftover = chunk[:max_bytes], chunk[max_bytes:]
                self._protocol.read_queue.appendleft(leftover)
            
            
            if not self._protocol.read_queue:
                self._protocol.read_event.clear()
        return chunk
    async def send(self, item: bytes) -> None:
        with self._send_guard:
            await AsyncIOBackend.checkpoint()
            if self._closed:
                raise ClosedResourceError
            elif self._protocol.exception is not None:
                raise self._protocol.exception
            try:
                self._transport.write(item)
            except RuntimeError as exc:
                if self._transport.is_closing():
                    raise BrokenResourceError from exc
                else:
                    raise
            await self._protocol.write_event.wait()
    async def send_eof(self) -> None:
        try:
            self._transport.write_eof()
        except OSError:
            pass
    async def aclose(self) -> None:
        if not self._transport.is_closing():
            self._closed = True
            try:
                self._transport.write_eof()
            except OSError:
                pass
            self._transport.close()
            await sleep(0)
            self._transport.abort()
class _RawSocketMixin:
    _receive_future: asyncio.Future | None = None
    _send_future: asyncio.Future | None = None
    _closing = False
    def __init__(self, raw_socket: socket.socket):
        ...

    @property
    def _raw_socket(self) -> socket.socket:
        ...

    def _wait_until_readable(self, loop: asyncio.AbstractEventLoop) -> asyncio.Future:
        ...

    def _wait_until_writable(self, loop: asyncio.AbstractEventLoop) -> asyncio.Future:
        ...

    async def aclose(self) -> None:
        if not self._closing:
            self._closing = True
            if self.__raw_socket.fileno() != -1:
                self.__raw_socket.close()
            if self._receive_future:
                self._receive_future.set_result(None)
            if self._send_future:
                self._send_future.set_result(None)
class UNIXSocketStream(_RawSocketMixin, abc.UNIXSocketStream):
    async def send_eof(self) -> None:
        with self._send_guard:
            self._raw_socket.shutdown(socket.SHUT_WR)
    async def receive(self, max_bytes: int = 65536) -> bytes:
        loop = get_running_loop()
        await AsyncIOBackend.checkpoint()
        with self._receive_guard:
            while True:
                try:
                    data = self._raw_socket.recv(max_bytes)
                except BlockingIOError:
                    await self._wait_until_readable(loop)
                except OSError as exc:
                    if self._closing:
                        raise ClosedResourceError from None
                    else:
                        raise BrokenResourceError from exc
                else:
                    if not data:
                        raise EndOfStream
                    return data
    async def send(self, item: bytes) -> None:
        loop = get_running_loop()
        await AsyncIOBackend.checkpoint()
        with self._send_guard:
            view = memoryview(item)
            while view:
                try:
                    bytes_sent = self._raw_socket.send(view)
                except BlockingIOError:
                    await self._wait_until_writable(loop)
                except OSError as exc:
                    if self._closing:
                        raise ClosedResourceError from None
                    else:
                        raise BrokenResourceError from exc
                else:
                    view = view[bytes_sent:]
    async def receive_fds(self, msglen: int, maxfds: int) -> tuple[bytes, list[int]]:
        if not isinstance(msglen, int) or msglen < 0:
            raise ValueError("msglen must be a non-negative integer")
        if not isinstance(maxfds, int) or maxfds < 1:
            raise ValueError("maxfds must be a positive integer")
        loop = get_running_loop()
        fds = array.array("i")
        await AsyncIOBackend.checkpoint()
        with self._receive_guard:
            while True:
                try:
                    message, ancdata, flags, addr = self._raw_socket.recvmsg(
                        msglen, socket.CMSG_LEN(maxfds * fds.itemsize)
                    )
                except BlockingIOError:
                    await self._wait_until_readable(loop)
                except OSError as exc:
                    if self._closing:
                        raise ClosedResourceError from None
                    else:
                        raise BrokenResourceError from exc
                else:
                    if not message and not ancdata:
                        raise EndOfStream
                    break
        for cmsg_level, cmsg_type, cmsg_data in ancdata:
            if cmsg_level != socket.SOL_SOCKET or cmsg_type != socket.SCM_RIGHTS:
                raise RuntimeError(
                    f"Received unexpected ancillary data; message = {message!r}, "
                    f"cmsg_level = {cmsg_level}, cmsg_type = {cmsg_type}"
                )
            fds.frombytes(cmsg_data[: len(cmsg_data) - (len(cmsg_data) % fds.itemsize)])
        return message, list(fds)
    async def send_fds(self, message: bytes, fds: Collection[int | IOBase]) -> None:
        if not message:
            raise ValueError("message must not be empty")
        if not fds:
            raise ValueError("fds must not be empty")
        loop = get_running_loop()
        filenos: list[int] = []
        for fd in fds:
            if isinstance(fd, int):
                filenos.append(fd)
            elif isinstance(fd, IOBase):
                filenos.append(fd.fileno())
        fdarray = array.array("i", filenos)
        await AsyncIOBackend.checkpoint()
        with self._send_guard:
            while True:
                try:
                    
                    
                    self._raw_socket.sendmsg(
                        [message], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, fdarray)]
                    )
                    break
                except BlockingIOError:
                    await self._wait_until_writable(loop)
                except OSError as exc:
                    if self._closing:
                        raise ClosedResourceError from None
                    else:
                        raise BrokenResourceError from exc
class TCPSocketListener(abc.SocketListener):
    _accept_scope: CancelScope | None = None
    _closed = False
    def __init__(self, raw_socket: socket.socket):
        ...

    @property
    def _raw_socket(self) -> socket.socket:
        ...

    async def accept(self) -> abc.SocketStream:
        if self._closed:
            raise ClosedResourceError
        with self._accept_guard:
            await AsyncIOBackend.checkpoint()
            with CancelScope() as self._accept_scope:
                try:
                    client_sock, _addr = await self._loop.sock_accept(self._raw_socket)
                except asyncio.CancelledError:
                    
                    try:
                        self._loop.remove_reader(self._raw_socket)
                    except (ValueError, NotImplementedError):
                        pass
                    if self._closed:
                        raise ClosedResourceError from None
                    raise
                finally:
                    self._accept_scope = None
        client_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        transport, protocol = await self._loop.connect_accepted_socket(
            StreamProtocol, client_sock
        )
        return SocketStream(transport, protocol)
    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._accept_scope:
            
            try:
                self._loop.remove_reader(self._raw_socket)
            except (ValueError, NotImplementedError):
                pass
            self._accept_scope.cancel()
            await sleep(0)
        self._raw_socket.close()
class UNIXSocketListener(abc.SocketListener):
    def __init__(self, raw_socket: socket.socket):
        ...

    async def accept(self) -> abc.SocketStream:
        await AsyncIOBackend.checkpoint()
        with self._accept_guard:
            while True:
                try:
                    client_sock, _ = self.__raw_socket.accept()
                    client_sock.setblocking(False)
                    return UNIXSocketStream(client_sock)
                except BlockingIOError:
                    f: asyncio.Future = asyncio.Future()
                    self._loop.add_reader(self.__raw_socket, f.set_result, None)
                    f.add_done_callback(
                        lambda _: self._loop.remove_reader(self.__raw_socket)
                    )
                    await f
                except OSError as exc:
                    if self._closed:
                        raise ClosedResourceError from None
                    else:
                        raise BrokenResourceError from exc
    async def aclose(self) -> None:
        self._closed = True
        self.__raw_socket.close()
    @property
    def _raw_socket(self) -> socket.socket:
        ...

class UDPSocket(abc.UDPSocket):
    def __init__(
        self, transport: asyncio.DatagramTransport, protocol: DatagramProtocol
    ):
        ...

    @property
    def _raw_socket(self) -> socket.socket:
        ...

    async def aclose(self) -> None:
        if not self._transport.is_closing():
            self._closed = True
            self._transport.close()
    async def receive(self) -> tuple[bytes, IPSockAddrType]:
        with self._receive_guard:
            await AsyncIOBackend.checkpoint()
            
            if not self._protocol.read_queue and not self._transport.is_closing():
                self._protocol.read_event.clear()
                await self._protocol.read_event.wait()
            try:
                return self._protocol.read_queue.popleft()
            except IndexError:
                if self._closed:
                    raise ClosedResourceError from None
                else:
                    raise BrokenResourceError from None
    async def send(self, item: UDPPacketType) -> None:
        with self._send_guard:
            await AsyncIOBackend.checkpoint()
            await self._protocol.write_event.wait()
            if self._closed:
                raise ClosedResourceError
            elif self._transport.is_closing():
                raise BrokenResourceError
            else:
                self._transport.sendto(*item)
class ConnectedUDPSocket(abc.ConnectedUDPSocket):
    def __init__(
        self, transport: asyncio.DatagramTransport, protocol: DatagramProtocol
    ):
        ...

    @property
    def _raw_socket(self) -> socket.socket:
        ...

    async def aclose(self) -> None:
        if not self._transport.is_closing():
            self._closed = True
            self._transport.close()
    async def receive(self) -> bytes:
        with self._receive_guard:
            await AsyncIOBackend.checkpoint()
            
            if not self._protocol.read_queue and not self._transport.is_closing():
                self._protocol.read_event.clear()
                await self._protocol.read_event.wait()
            try:
                packet = self._protocol.read_queue.popleft()
            except IndexError:
                if self._closed:
                    raise ClosedResourceError from None
                else:
                    raise BrokenResourceError from None
            return packet[0]
    async def send(self, item: bytes) -> None:
        with self._send_guard:
            await AsyncIOBackend.checkpoint()
            await self._protocol.write_event.wait()
            if self._closed:
                raise ClosedResourceError
            elif self._transport.is_closing():
                raise BrokenResourceError
            else:
                self._transport.sendto(item)
class UNIXDatagramSocket(_RawSocketMixin, abc.UNIXDatagramSocket):
    async def receive(self) -> UNIXDatagramPacketType:
        loop = get_running_loop()
        await AsyncIOBackend.checkpoint()
        with self._receive_guard:
            while True:
                try:
                    data = self._raw_socket.recvfrom(65536)
                except BlockingIOError:
                    await self._wait_until_readable(loop)
                except OSError as exc:
                    if self._closing:
                        raise ClosedResourceError from None
                    else:
                        raise BrokenResourceError from exc
                else:
                    return data
    async def send(self, item: UNIXDatagramPacketType) -> None:
        loop = get_running_loop()
        await AsyncIOBackend.checkpoint()
        with self._send_guard:
            while True:
                try:
                    self._raw_socket.sendto(*item)
                except BlockingIOError:
                    await self._wait_until_writable(loop)
                except OSError as exc:
                    if self._closing:
                        raise ClosedResourceError from None
                    else:
                        raise BrokenResourceError from exc
                else:
                    return
class ConnectedUNIXDatagramSocket(_RawSocketMixin, abc.ConnectedUNIXDatagramSocket):
    async def receive(self) -> bytes:
        loop = get_running_loop()
        await AsyncIOBackend.checkpoint()
        with self._receive_guard:
            while True:
                try:
                    data = self._raw_socket.recv(65536)
                except BlockingIOError:
                    await self._wait_until_readable(loop)
                except OSError as exc:
                    if self._closing:
                        raise ClosedResourceError from None
                    else:
                        raise BrokenResourceError from exc
                else:
                    return data
    async def send(self, item: bytes) -> None:
        loop = get_running_loop()
        await AsyncIOBackend.checkpoint()
        with self._send_guard:
            while True:
                try:
                    self._raw_socket.send(item)
                except BlockingIOError:
                    await self._wait_until_writable(loop)
                except OSError as exc:
                    if self._closing:
                        raise ClosedResourceError from None
                    else:
                        raise BrokenResourceError from exc
                else:
                    return
_read_events: RunVar[dict[int, asyncio.Future[bool]]] = RunVar("read_events")
_write_events: RunVar[dict[int, asyncio.Future[bool]]] = RunVar("write_events")
class Event(BaseEvent):
    def __new__(cls) -> Event:
        ...

    def __init__(self) -> None:
        ...

    def set(self) -> None:
        ...

    def is_set(self) -> bool:
        ...

    async def wait(self) -> None:
        if self.is_set():
            await AsyncIOBackend.checkpoint()
        else:
            await self._event.wait()
    def statistics(self) -> EventStatistics:
        ...

class Lock(BaseLock):
    def __new__(cls, *, fast_acquire: bool = False) -> Lock:
        ...

    def __init__(self, *, fast_acquire: bool = False) -> None:
        ...

    async def acquire(self) -> None:
        task = cast(asyncio.Task, current_task())
        if self._owner_task is None and not self._waiters:
            await AsyncIOBackend.checkpoint_if_cancelled()
            self._owner_task = task
            
            
            if not self._fast_acquire:
                try:
                    await AsyncIOBackend.cancel_shielded_checkpoint()
                except CancelledError:
                    self.release()
                    raise
            return
        if self._owner_task == task:
            raise RuntimeError("Attempted to acquire an already held Lock")
        fut: asyncio.Future[None] = asyncio.Future()
        item = task, fut
        self._waiters.append(item)
        try:
            await fut
        except CancelledError:
            self._waiters.remove(item)
            if self._owner_task is task:
                self.release()
            raise
        self._waiters.remove(item)
    def acquire_nowait(self) -> None:
        ...

    def locked(self) -> bool:
        ...

    def release(self) -> None:
        ...

    def statistics(self) -> LockStatistics:
        ...

class Semaphore(BaseSemaphore):
    def __new__(
        cls,
        initial_value: int,
        *,
        max_value: int | None = None,
        fast_acquire: bool = False,
    ) -> Semaphore:
        ...

    def __init__(
        self,
        initial_value: int,
        *,
        max_value: int | None = None,
        fast_acquire: bool = False,
    ):
        ...

    async def acquire(self) -> None:
        if self._value > 0 and not self._waiters:
            await AsyncIOBackend.checkpoint_if_cancelled()
            self._value -= 1
            
            
            if not self._fast_acquire:
                try:
                    await AsyncIOBackend.cancel_shielded_checkpoint()
                except CancelledError:
                    self.release()
                    raise
            return
        fut: asyncio.Future[None] = asyncio.Future()
        self._waiters.append(fut)
        try:
            await fut
        except CancelledError:
            try:
                self._waiters.remove(fut)
            except ValueError:
                self.release()
            raise
    def acquire_nowait(self) -> None:
        ...

    def release(self) -> None:
        ...

    @property
    def value(self) -> int:
        ...

    @property
    def max_value(self) -> int | None:
        ...

    def statistics(self) -> SemaphoreStatistics:
        ...

class CapacityLimiter(BaseCapacityLimiter):
    _total_tokens: float = 0
    def __new__(cls, total_tokens: float) -> CapacityLimiter:
        ...

    def __init__(self, total_tokens: float):
        ...

    async def __aenter__(self) -> None:
        await self.acquire()
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.release()
    @property
    def total_tokens(self) -> float:
        ...

    @total_tokens.setter
    def total_tokens(self, value: float) -> None:
        ...

    @property
    def borrowed_tokens(self) -> int:
        ...

    @property
    def available_tokens(self) -> float:
        ...

    def acquire_nowait(self) -> None:
        ...

    def acquire_on_behalf_of_nowait(self, borrower: object) -> None:
        ...

    async def acquire(self) -> None:
        return await self.acquire_on_behalf_of(current_task())
    async def acquire_on_behalf_of(self, borrower: object) -> None:
        await AsyncIOBackend.checkpoint_if_cancelled()
        try:
            self.acquire_on_behalf_of_nowait(borrower)
        except WouldBlock:
            event = asyncio.Event()
            self._wait_queue[borrower] = event
            try:
                await event.wait()
            except BaseException:
                self._wait_queue.pop(borrower, None)
                raise
            self._borrowers.add(borrower)
        else:
            try:
                await AsyncIOBackend.cancel_shielded_checkpoint()
            except BaseException:
                self.release()
                raise
    def release(self) -> None:
        ...

    def release_on_behalf_of(self, borrower: object) -> None:
        ...

    def statistics(self) -> CapacityLimiterStatistics:
        ...

_default_thread_limiter: RunVar[CapacityLimiter] = RunVar("_default_thread_limiter")
class _SignalReceiver:
    def __init__(self, signals: tuple[Signals, ...]):
        ...

    def _deliver(self, signum: Signals) -> None:
        ...

    def __enter__(self) -> _SignalReceiver:
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        ...

    def __aiter__(self) -> _SignalReceiver:
        ...

    async def __anext__(self) -> Signals:
        await AsyncIOBackend.checkpoint()
        if not self._signal_queue:
            self._future = asyncio.Future()
            await self._future
        return self._signal_queue.popleft()
class AsyncIOTaskInfo(TaskInfo):
    def __init__(self, task: asyncio.Task):
        ...

    def has_pending_cancellation(self) -> bool:
        ...

class TestRunner(abc.TestRunner):
    _send_stream: MemoryObjectSendStream[tuple[Awaitable[Any], asyncio.Future[Any]]]
    def __init__(
        self,
        *,
        debug: bool | None = None,
        use_uvloop: bool = False,
        loop_factory: Callable[[], AbstractEventLoop] | None = None,
    ) -> None:
        ...

    def __enter__(self) -> TestRunner:
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        ...

    def get_loop(self) -> AbstractEventLoop:
        ...

    def _exception_handler(
        self, loop: asyncio.AbstractEventLoop, context: dict[str, Any]
    ) -> None:
        ...

    def _raise_async_exceptions(self) -> None:
        ...

    async def _run_tests_and_fixtures(
        self,
        receive_stream: MemoryObjectReceiveStream[
            tuple[Awaitable[T_Retval], asyncio.Future[T_Retval]]
        ],
    ) -> None:
        from _pytest.outcomes import OutcomeException
        with receive_stream, self._send_stream:
            async for coro, future in receive_stream:
                try:
                    retval = await coro
                except CancelledError as exc:
                    if not future.cancelled():
                        future.cancel(*exc.args)
                    raise
                except BaseException as exc:
                    if not future.cancelled():
                        future.set_exception(exc)
                    if not isinstance(exc, (Exception, OutcomeException)):
                        raise
                else:
                    if not future.cancelled():
                        future.set_result(retval)
    async def _call_in_runner_task(
        self,
        func: Callable[P, Awaitable[T_Retval]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T_Retval:
        if not self._runner_task:
            self._send_stream, receive_stream = create_memory_object_stream[
                tuple[Awaitable[Any], asyncio.Future]
            ](1)
            self._runner_task = self.get_loop().create_task(
                self._run_tests_and_fixtures(receive_stream)
            )
        coro = func(*args, **kwargs)
        future: asyncio.Future[T_Retval] = self.get_loop().create_future()
        self._send_stream.send_nowait((coro, future))
        return await future
    def run_asyncgen_fixture(
        self,
        fixture_func: Callable[..., AsyncGenerator[T_Retval, Any]],
        kwargs: dict[str, Any],
    ) -> Iterable[T_Retval]:
        ...

    def run_fixture(
        self,
        fixture_func: Callable[..., Coroutine[Any, Any, T_Retval]],
        kwargs: dict[str, Any],
    ) -> T_Retval:
        ...

    def run_test(
        self, test_func: Callable[..., Coroutine[Any, Any, Any]], kwargs: dict[str, Any]
    ) -> None:
        ...

class AsyncIOBackend(AsyncBackend):
    @classmethod
    def run(
        cls,
        func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval]],
        args: tuple[Unpack[PosArgsT]],
        kwargs: dict[str, Any],
        options: dict[str, Any],
    ) -> T_Retval:
        ...

    @classmethod
    def current_token(cls) -> object:
        ...

    @classmethod
    def current_time(cls) -> float:
        ...

    @classmethod
    def cancelled_exception_class(cls) -> type[BaseException]:
        ...

    @classmethod
    async def checkpoint(cls) -> None:
        await sleep(0)
    @classmethod
    async def checkpoint_if_cancelled(cls) -> None:
        task = current_task()
        if task is None:
            return
        try:
            cancel_scope = _task_states[task].cancel_scope
        except KeyError:
            return
        while cancel_scope:
            if cancel_scope.cancel_called:
                await sleep(0)
            elif cancel_scope.shield:
                break
            else:
                cancel_scope = cancel_scope._parent_scope
    @classmethod
    async def cancel_shielded_checkpoint(cls) -> None:
        with CancelScope(shield=True):
            await sleep(0)
    @classmethod
    async def sleep(cls, delay: float) -> None:
        await sleep(delay)
    @classmethod
    def create_cancel_scope(
        cls, *, deadline: float = math.inf, shield: bool = False
    ) -> CancelScope:
        ...

    @classmethod
    def current_effective_deadline(cls) -> float:
        ...

    @classmethod
    def create_task_group(cls) -> abc.TaskGroup:
        ...

    @classmethod
    def create_event(cls) -> abc.Event:
        ...

    @classmethod
    def create_lock(cls, *, fast_acquire: bool) -> abc.Lock:
        ...

    @classmethod
    def create_semaphore(
        cls,
        initial_value: int,
        *,
        max_value: int | None = None,
        fast_acquire: bool = False,
    ) -> abc.Semaphore:
        ...

    @classmethod
    def create_capacity_limiter(cls, total_tokens: float) -> abc.CapacityLimiter:
        ...

    @classmethod
    async def run_sync_in_worker_thread(  
        cls,
        func: Callable[[Unpack[PosArgsT]], T_Retval],
        args: tuple[Unpack[PosArgsT]],
        abandon_on_cancel: bool = False,
        limiter: abc.CapacityLimiter | None = None,
    ) -> T_Retval:
        await cls.checkpoint()
        
        
        try:
            idle_workers = _threadpool_idle_workers.get()
            workers = _threadpool_workers.get()
        except LookupError:
            idle_workers = deque()
            workers = set()
            _threadpool_idle_workers.set(idle_workers)
            _threadpool_workers.set(workers)
        async with limiter or cls.current_default_thread_limiter():
            with CancelScope(shield=not abandon_on_cancel) as scope:
                future = asyncio.Future[T_Retval]()
                root_task = find_root_task()
                if not idle_workers:
                    worker = WorkerThread(root_task, workers, idle_workers)
                    worker.start()
                    workers.add(worker)
                    root_task.add_done_callback(
                        worker.stop, context=contextvars.Context()
                    )
                else:
                    worker = idle_workers.pop()
                    
                    
                    now = cls.current_time()
                    while idle_workers:
                        if (
                            now - idle_workers[0].idle_since
                            < WorkerThread.MAX_IDLE_TIME
                        ):
                            break
                        expired_worker = idle_workers.popleft()
                        expired_worker.root_task.remove_done_callback(
                            expired_worker.stop
                        )
                        expired_worker.stop()
                context = copy_context()
                context.run(sniffio.current_async_library_cvar.set, None)
                if abandon_on_cancel or scope._parent_scope is None:
                    worker_scope = scope
                else:
                    worker_scope = scope._parent_scope
                worker.queue.put_nowait((context, func, args, future, worker_scope))
                return await future
    @classmethod
    def check_cancelled(cls) -> None:
        ...

    @classmethod
    def run_async_from_thread(
        cls,
        func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval]],
        args: tuple[Unpack[PosArgsT]],
        token: object,
    ) -> T_Retval:
        ...

    @classmethod
    def run_sync_from_thread(
        cls,
        func: Callable[[Unpack[PosArgsT]], T_Retval],
        args: tuple[Unpack[PosArgsT]],
        token: object,
    ) -> T_Retval:
        ...

    @classmethod
    def create_blocking_portal(cls) -> abc.BlockingPortal:
        ...

    @classmethod
    async def open_process(
        cls,
        command: StrOrBytesPath | Sequence[StrOrBytesPath],
        *,
        stdin: int | IO[Any] | None,
        stdout: int | IO[Any] | None,
        stderr: int | IO[Any] | None,
        **kwargs: Any,
    ) -> Process:
        await cls.checkpoint()
        if isinstance(command, PathLike):
            command = os.fspath(command)
        if isinstance(command, (str, bytes)):
            process = await asyncio.create_subprocess_shell(
                command,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                **kwargs,
            )
        else:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                **kwargs,
            )
        stdin_stream = StreamWriterWrapper(process.stdin) if process.stdin else None
        stdout_stream = StreamReaderWrapper(process.stdout) if process.stdout else None
        stderr_stream = StreamReaderWrapper(process.stderr) if process.stderr else None
        return Process(process, stdin_stream, stdout_stream, stderr_stream)
    @classmethod
    def setup_process_pool_exit_at_shutdown(cls, workers: set[abc.Process]) -> None:
        ...

    @classmethod
    async def connect_tcp(
        cls, host: str, port: int, local_address: IPSockAddrType | None = None
    ) -> abc.SocketStream:
        transport, protocol = cast(
            tuple[asyncio.Transport, StreamProtocol],
            await get_running_loop().create_connection(
                StreamProtocol, host, port, local_addr=local_address
            ),
        )
        transport.pause_reading()
        return SocketStream(transport, protocol)
    @classmethod
    async def connect_unix(cls, path: str | bytes) -> abc.UNIXSocketStream:
        await cls.checkpoint()
        loop = get_running_loop()
        raw_socket = socket.socket(socket.AF_UNIX)
        raw_socket.setblocking(False)
        while True:
            try:
                raw_socket.connect(path)
            except BlockingIOError:
                f: asyncio.Future = asyncio.Future()
                loop.add_writer(raw_socket, f.set_result, None)
                f.add_done_callback(lambda _: loop.remove_writer(raw_socket))
                await f
            except BaseException:
                raw_socket.close()
                raise
            else:
                return UNIXSocketStream(raw_socket)
    @classmethod
    def create_tcp_listener(cls, sock: socket.socket) -> SocketListener:
        ...

    @classmethod
    def create_unix_listener(cls, sock: socket.socket) -> SocketListener:
        ...

    @classmethod
    async def create_udp_socket(
        cls,
        family: AddressFamily,
        local_address: IPSockAddrType | None,
        remote_address: IPSockAddrType | None,
        reuse_port: bool,
    ) -> UDPSocket | ConnectedUDPSocket:
        transport, protocol = await get_running_loop().create_datagram_endpoint(
            DatagramProtocol,
            local_addr=local_address,
            remote_addr=remote_address,
            family=family,
            reuse_port=reuse_port,
        )
        if protocol.exception:
            transport.close()
            raise protocol.exception
        if not remote_address:
            return UDPSocket(transport, protocol)
        else:
            return ConnectedUDPSocket(transport, protocol)
    @classmethod
    async def create_unix_datagram_socket(  
        cls, raw_socket: socket.socket, remote_path: str | bytes | None
    ) -> abc.UNIXDatagramSocket | abc.ConnectedUNIXDatagramSocket:
        await cls.checkpoint()
        loop = get_running_loop()
        if remote_path:
            while True:
                try:
                    raw_socket.connect(remote_path)
                except BlockingIOError:
                    f: asyncio.Future = asyncio.Future()
                    loop.add_writer(raw_socket, f.set_result, None)
                    f.add_done_callback(lambda _: loop.remove_writer(raw_socket))
                    await f
                except BaseException:
                    raw_socket.close()
                    raise
                else:
                    return ConnectedUNIXDatagramSocket(raw_socket)
        else:
            return UNIXDatagramSocket(raw_socket)
    @classmethod
    async def getaddrinfo(
        cls,
        host: bytes | str | None,
        port: str | int | None,
        *,
        family: int | AddressFamily = 0,
        type: int | SocketKind = 0,
        proto: int = 0,
        flags: int = 0,
    ) -> Sequence[
        tuple[
            AddressFamily,
            SocketKind,
            int,
            str,
            tuple[str, int] | tuple[str, int, int, int] | tuple[int, bytes],
        ]
    ]:
        return await get_running_loop().getaddrinfo(
            host, port, family=family, type=type, proto=proto, flags=flags
        )
    @classmethod
    async def getnameinfo(
        cls, sockaddr: IPSockAddrType, flags: int = 0
    ) -> tuple[str, str]:
        return await get_running_loop().getnameinfo(sockaddr, flags)
    @classmethod
    async def wait_readable(cls, obj: FileDescriptorLike) -> None:
        try:
            read_events = _read_events.get()
        except LookupError:
            read_events = {}
            _read_events.set(read_events)
        fd = obj if isinstance(obj, int) else obj.fileno()
        if read_events.get(fd):
            raise BusyResourceError("reading from")
        loop = get_running_loop()
        fut: asyncio.Future[bool] = loop.create_future()
        def cb() -> None:
            ...

        try:
            loop.add_reader(fd, cb)
        except NotImplementedError:
            from anyio._core._asyncio_selector_thread import get_selector
            selector = get_selector()
            selector.add_reader(fd, cb)
            remove_reader = selector.remove_reader
        else:
            remove_reader = loop.remove_reader
        read_events[fd] = fut
        try:
            success = await fut
        finally:
            try:
                del read_events[fd]
            except KeyError:
                pass
            else:
                remove_reader(fd)
        if not success:
            raise ClosedResourceError
    @classmethod
    async def wait_writable(cls, obj: FileDescriptorLike) -> None:
        try:
            write_events = _write_events.get()
        except LookupError:
            write_events = {}
            _write_events.set(write_events)
        fd = obj if isinstance(obj, int) else obj.fileno()
        if write_events.get(fd):
            raise BusyResourceError("writing to")
        loop = get_running_loop()
        fut: asyncio.Future[bool] = loop.create_future()
        def cb() -> None:
            ...

        try:
            loop.add_writer(fd, cb)
        except NotImplementedError:
            from anyio._core._asyncio_selector_thread import get_selector
            selector = get_selector()
            selector.add_writer(fd, cb)
            remove_writer = selector.remove_writer
        else:
            remove_writer = loop.remove_writer
        write_events[fd] = fut
        try:
            success = await fut
        finally:
            try:
                del write_events[fd]
            except KeyError:
                pass
            else:
                remove_writer(fd)
        if not success:
            raise ClosedResourceError
    @classmethod
    def notify_closing(cls, obj: FileDescriptorLike) -> None:
        ...

    @classmethod
    async def wrap_listener_socket(cls, sock: socket.socket) -> SocketListener:
        return TCPSocketListener(sock)
    @classmethod
    async def wrap_stream_socket(cls, sock: socket.socket) -> SocketStream:
        transport, protocol = await get_running_loop().create_connection(
            StreamProtocol, sock=sock
        )
        return SocketStream(transport, protocol)
    @classmethod
    async def wrap_unix_stream_socket(cls, sock: socket.socket) -> UNIXSocketStream:
        return UNIXSocketStream(sock)
    @classmethod
    async def wrap_udp_socket(cls, sock: socket.socket) -> UDPSocket:
        transport, protocol = await get_running_loop().create_datagram_endpoint(
            DatagramProtocol, sock=sock
        )
        return UDPSocket(transport, protocol)
    @classmethod
    async def wrap_connected_udp_socket(cls, sock: socket.socket) -> ConnectedUDPSocket:
        transport, protocol = await get_running_loop().create_datagram_endpoint(
            DatagramProtocol, sock=sock
        )
        return ConnectedUDPSocket(transport, protocol)
    @classmethod
    async def wrap_unix_datagram_socket(cls, sock: socket.socket) -> UNIXDatagramSocket:
        return UNIXDatagramSocket(sock)
    @classmethod
    async def wrap_connected_unix_datagram_socket(
        cls, sock: socket.socket
    ) -> ConnectedUNIXDatagramSocket:
        return ConnectedUNIXDatagramSocket(sock)
    @classmethod
    def current_default_thread_limiter(cls) -> CapacityLimiter:
        ...

    @classmethod
    def open_signal_receiver(
        cls, *signals: Signals
    ) -> AbstractContextManager[AsyncIterator[Signals]]:
        ...

    @classmethod
    def get_current_task(cls) -> TaskInfo:
        ...

    @classmethod
    def get_running_tasks(cls) -> Sequence[TaskInfo]:
        ...

    @classmethod
    async def wait_all_tasks_blocked(cls) -> None:
        await cls.checkpoint()
        this_task = current_task()
        while True:
            for task in all_tasks():
                if task is this_task:
                    continue
                waiter = task._fut_waiter  
                if waiter is None or waiter.done():
                    await sleep(0.1)
                    break
            else:
                return
    @classmethod
    def create_test_runner(cls, options: dict[str, Any]) -> TestRunner:
        ...

backend_class = AsyncIOBackend
