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
import math
import os
import socket
import sys
import types
import weakref
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
from contextlib import AbstractContextManager
from dataclasses import dataclass
from functools import partial
from io import IOBase
from os import PathLike
from signal import Signals
from socket import AddressFamily, SocketKind
from types import TracebackType
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    Generic,
    NoReturn,
    TypeVar,
    cast,
    overload,
)
import trio.from_thread
import trio.lowlevel
from outcome import Error, Outcome, Value
from trio.lowlevel import (
    current_root_task,
    current_task,
    notify_closing,
    wait_readable,
    wait_writable,
)
from trio.socket import SocketType as TrioSocketType
from trio.to_thread import run_sync
from .. import (
    CapacityLimiterStatistics,
    EventStatistics,
    LockStatistics,
    TaskInfo,
    WouldBlock,
    abc,
)
from .._core._eventloop import claim_worker_thread
from .._core._exceptions import (
    BrokenResourceError,
    BusyResourceError,
    ClosedResourceError,
    EndOfStream,
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
from ..abc import IPSockAddrType, UDPPacketType, UNIXDatagramPacketType
from ..abc._eventloop import AsyncBackend, StrOrBytesPath
from ..streams.memory import MemoryObjectSendStream
if TYPE_CHECKING:
    from _typeshed import FileDescriptorLike
if sys.version_info >= (3, 10):
    from typing import ParamSpec
else:
    from typing_extensions import ParamSpec
if sys.version_info >= (3, 11):
    from typing import TypeVarTuple, Unpack
else:
    from exceptiongroup import BaseExceptionGroup
    from typing_extensions import TypeVarTuple, Unpack
T = TypeVar("T")
T_Retval = TypeVar("T_Retval")
T_SockAddr = TypeVar("T_SockAddr", str, IPSockAddrType)
PosArgsT = TypeVarTuple("PosArgsT")
P = ParamSpec("P")
RunVar = trio.lowlevel.RunVar
class CancelScope(BaseCancelScope):
    def __new__(
        cls, original: trio.CancelScope | None = None, **kwargs: object
    ) -> CancelScope:
        ...

    def __init__(self, original: trio.CancelScope | None = None, **kwargs: Any) -> None:
        ...

    def __enter__(self) -> CancelScope:
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        ...

    def cancel(self) -> None:
        ...

    @property
    def deadline(self) -> float:
        ...

    @deadline.setter
    def deadline(self, value: float) -> None:
        ...

    @property
    def cancel_called(self) -> bool:
        ...

    @property
    def cancelled_caught(self) -> bool:
        ...

    @property
    def shield(self) -> bool:
        ...

    @shield.setter
    def shield(self, value: bool) -> None:
        ...

class TaskGroup(abc.TaskGroup):
    def __init__(self) -> None:
        ...

    async def __aenter__(self) -> TaskGroup:
        self._active = True
        self._nursery = await self._nursery_manager.__aenter__()
        self.cancel_scope = CancelScope(self._nursery.cancel_scope)
        return self
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        try:
            return await self._nursery_manager.__aexit__(exc_type, exc_val, exc_tb)  
        except BaseExceptionGroup as exc:
            if not exc.split(trio.Cancelled)[1]:
                raise trio.Cancelled._create() from exc
            raise
        finally:
            del exc_val, exc_tb
            self._active = False
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
        if not self._active:
            raise RuntimeError(
                "This task group is not active; no new tasks can be started."
            )
        return await self._nursery.start(func, *args, name=name)
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
class ReceiveStreamWrapper(abc.ByteReceiveStream):
    _stream: trio.abc.ReceiveStream
    async def receive(self, max_bytes: int | None = None) -> bytes:
        try:
            data = await self._stream.receive_some(max_bytes)
        except trio.ClosedResourceError as exc:
            raise ClosedResourceError from exc.__cause__
        except trio.BrokenResourceError as exc:
            raise BrokenResourceError from exc.__cause__
        if data:
            return bytes(data)
        else:
            raise EndOfStream
    async def aclose(self) -> None:
        await self._stream.aclose()
@dataclass(eq=False)
class SendStreamWrapper(abc.ByteSendStream):
    _stream: trio.abc.SendStream
    async def send(self, item: bytes) -> None:
        try:
            await self._stream.send_all(item)
        except trio.ClosedResourceError as exc:
            raise ClosedResourceError from exc.__cause__
        except trio.BrokenResourceError as exc:
            raise BrokenResourceError from exc.__cause__
    async def aclose(self) -> None:
        await self._stream.aclose()
@dataclass(eq=False)
class Process(abc.Process):
    _process: trio.Process
    _stdin: abc.ByteSendStream | None
    _stdout: abc.ByteReceiveStream | None
    _stderr: abc.ByteReceiveStream | None
    async def aclose(self) -> None:
        with CancelScope(shield=True):
            if self._stdin:
                await self._stdin.aclose()
            if self._stdout:
                await self._stdout.aclose()
            if self._stderr:
                await self._stderr.aclose()
        try:
            await self.wait()
        except BaseException:
            self.kill()
            with CancelScope(shield=True):
                await self.wait()
            raise
    async def wait(self) -> int:
        return await self._process.wait()
    def terminate(self) -> None:
        ...

    def kill(self) -> None:
        ...

    def send_signal(self, signal: Signals) -> None:
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

class _ProcessPoolShutdownInstrument(trio.abc.Instrument):
    def after_run(self) -> None:
        ...

current_default_worker_process_limiter: trio.lowlevel.RunVar = RunVar(
    "current_default_worker_process_limiter"
)
async def _shutdown_process_pool(workers: set[abc.Process]) -> None:
    try:
        await trio.sleep(math.inf)
    except trio.Cancelled:
        for process in workers:
            if process.returncode is None:
                process.kill()
        with CancelScope(shield=True):
            for process in workers:
                await process.aclose()
class _TrioSocketMixin(Generic[T_SockAddr]):
    def __init__(self, trio_socket: TrioSocketType) -> None:
        ...

    def _check_closed(self) -> None:
        ...

    @property
    def _raw_socket(self) -> socket.socket:
        ...

    async def aclose(self) -> None:
        if self._trio_socket.fileno() >= 0:
            self._closed = True
            self._trio_socket.close()
    def _convert_socket_error(self, exc: BaseException) -> NoReturn:
        ...

class SocketStream(_TrioSocketMixin, abc.SocketStream):
    def __init__(self, trio_socket: TrioSocketType) -> None:
        ...

    async def receive(self, max_bytes: int = 65536) -> bytes:
        with self._receive_guard:
            try:
                data = await self._trio_socket.recv(max_bytes)
            except BaseException as exc:
                self._convert_socket_error(exc)
            if data:
                return data
            else:
                raise EndOfStream
    async def send(self, item: bytes) -> None:
        with self._send_guard:
            view = memoryview(item)
            while view:
                try:
                    bytes_sent = await self._trio_socket.send(view)
                except BaseException as exc:
                    self._convert_socket_error(exc)
                view = view[bytes_sent:]
    async def send_eof(self) -> None:
        self._trio_socket.shutdown(socket.SHUT_WR)
class UNIXSocketStream(SocketStream, abc.UNIXSocketStream):
    async def receive_fds(self, msglen: int, maxfds: int) -> tuple[bytes, list[int]]:
        if not isinstance(msglen, int) or msglen < 0:
            raise ValueError("msglen must be a non-negative integer")
        if not isinstance(maxfds, int) or maxfds < 1:
            raise ValueError("maxfds must be a positive integer")
        fds = array.array("i")
        await trio.lowlevel.checkpoint()
        with self._receive_guard:
            while True:
                try:
                    message, ancdata, flags, addr = await self._trio_socket.recvmsg(
                        msglen, socket.CMSG_LEN(maxfds * fds.itemsize)
                    )
                except BaseException as exc:
                    self._convert_socket_error(exc)
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
        filenos: list[int] = []
        for fd in fds:
            if isinstance(fd, int):
                filenos.append(fd)
            elif isinstance(fd, IOBase):
                filenos.append(fd.fileno())
        fdarray = array.array("i", filenos)
        await trio.lowlevel.checkpoint()
        with self._send_guard:
            while True:
                try:
                    await self._trio_socket.sendmsg(
                        [message],
                        [
                            (
                                socket.SOL_SOCKET,
                                socket.SCM_RIGHTS,
                                fdarray,
                            )
                        ],
                    )
                    break
                except BaseException as exc:
                    self._convert_socket_error(exc)
class TCPSocketListener(_TrioSocketMixin, abc.SocketListener):
    def __init__(self, raw_socket: socket.socket):
        ...

    async def accept(self) -> SocketStream:
        with self._accept_guard:
            try:
                trio_socket, _addr = await self._trio_socket.accept()
            except BaseException as exc:
                self._convert_socket_error(exc)
        trio_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        return SocketStream(trio_socket)
class UNIXSocketListener(_TrioSocketMixin, abc.SocketListener):
    def __init__(self, raw_socket: socket.socket):
        ...

    async def accept(self) -> UNIXSocketStream:
        with self._accept_guard:
            try:
                trio_socket, _addr = await self._trio_socket.accept()
            except BaseException as exc:
                self._convert_socket_error(exc)
        return UNIXSocketStream(trio_socket)
class UDPSocket(_TrioSocketMixin[IPSockAddrType], abc.UDPSocket):
    def __init__(self, trio_socket: TrioSocketType) -> None:
        ...

    async def receive(self) -> tuple[bytes, IPSockAddrType]:
        with self._receive_guard:
            try:
                data, addr = await self._trio_socket.recvfrom(65536)
                return data, convert_ipv6_sockaddr(addr)
            except BaseException as exc:
                self._convert_socket_error(exc)
    async def send(self, item: UDPPacketType) -> None:
        with self._send_guard:
            try:
                await self._trio_socket.sendto(*item)
            except BaseException as exc:
                self._convert_socket_error(exc)
class ConnectedUDPSocket(_TrioSocketMixin[IPSockAddrType], abc.ConnectedUDPSocket):
    def __init__(self, trio_socket: TrioSocketType) -> None:
        ...

    async def receive(self) -> bytes:
        with self._receive_guard:
            try:
                return await self._trio_socket.recv(65536)
            except BaseException as exc:
                self._convert_socket_error(exc)
    async def send(self, item: bytes) -> None:
        with self._send_guard:
            try:
                await self._trio_socket.send(item)
            except BaseException as exc:
                self._convert_socket_error(exc)
class UNIXDatagramSocket(_TrioSocketMixin[str], abc.UNIXDatagramSocket):
    def __init__(self, trio_socket: TrioSocketType) -> None:
        ...

    async def receive(self) -> UNIXDatagramPacketType:
        with self._receive_guard:
            try:
                data, addr = await self._trio_socket.recvfrom(65536)
                return data, addr
            except BaseException as exc:
                self._convert_socket_error(exc)
    async def send(self, item: UNIXDatagramPacketType) -> None:
        with self._send_guard:
            try:
                await self._trio_socket.sendto(*item)
            except BaseException as exc:
                self._convert_socket_error(exc)
class ConnectedUNIXDatagramSocket(
    _TrioSocketMixin[str], abc.ConnectedUNIXDatagramSocket
):
    def __init__(self, trio_socket: TrioSocketType) -> None:
        ...

    async def receive(self) -> bytes:
        with self._receive_guard:
            try:
                return await self._trio_socket.recv(65536)
            except BaseException as exc:
                self._convert_socket_error(exc)
    async def send(self, item: bytes) -> None:
        with self._send_guard:
            try:
                await self._trio_socket.send(item)
            except BaseException as exc:
                self._convert_socket_error(exc)
class Event(BaseEvent):
    def __new__(cls) -> Event:
        ...

    def __init__(self) -> None:
        ...

    def is_set(self) -> bool:
        ...

    async def wait(self) -> None:
        return await self.__original.wait()
    def statistics(self) -> EventStatistics:
        ...

    def set(self) -> None:
        ...

class Lock(BaseLock):
    def __new__(cls, *, fast_acquire: bool = False) -> Lock:
        ...

    def __init__(self, *, fast_acquire: bool = False) -> None:
        ...

    @staticmethod
    def _convert_runtime_error_msg(exc: RuntimeError) -> None:
        ...

    async def acquire(self) -> None:
        if not self._fast_acquire:
            try:
                await self.__original.acquire()
            except RuntimeError as exc:
                self._convert_runtime_error_msg(exc)
                raise
            return
        await trio.lowlevel.checkpoint_if_cancelled()
        try:
            self.__original.acquire_nowait()
        except trio.WouldBlock:
            await self.__original._lot.park()
        except RuntimeError as exc:
            self._convert_runtime_error_msg(exc)
            raise
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
    ) -> None:
        ...

    async def acquire(self) -> None:
        if not self._fast_acquire:
            await self.__original.acquire()
            return
        await trio.lowlevel.checkpoint_if_cancelled()
        try:
            self.__original.acquire_nowait()
        except trio.WouldBlock:
            await self.__original._lot.park()
    def acquire_nowait(self) -> None:
        ...

    @property
    def max_value(self) -> int | None:
        ...

    @property
    def value(self) -> int:
        ...

    def release(self) -> None:
        ...

    def statistics(self) -> SemaphoreStatistics:
        ...

class CapacityLimiter(BaseCapacityLimiter):
    def __new__(
        cls,
        total_tokens: float | None = None,
        *,
        original: trio.CapacityLimiter | None = None,
    ) -> CapacityLimiter:
        ...

    def __init__(
        self,
        total_tokens: float | None = None,
        *,
        original: trio.CapacityLimiter | None = None,
    ) -> None:
        ...

    async def __aenter__(self) -> None:
        return await self.__original.__aenter__()
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.__original.__aexit__(exc_type, exc_val, exc_tb)
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
        await self.__original.acquire()
    async def acquire_on_behalf_of(self, borrower: object) -> None:
        await self.__original.acquire_on_behalf_of(borrower)
    def release(self) -> None:
        ...

    def release_on_behalf_of(self, borrower: object) -> None:
        ...

    def statistics(self) -> CapacityLimiterStatistics:
        ...

_capacity_limiter_wrapper: trio.lowlevel.RunVar = RunVar("_capacity_limiter_wrapper")
class _SignalReceiver:
    _iterator: AsyncIterator[int]
    def __init__(self, signals: tuple[Signals, ...]):
        ...

    def __enter__(self) -> _SignalReceiver:
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        ...

    def __aiter__(self) -> _SignalReceiver:
        ...

    async def __anext__(self) -> Signals:
        signum = await self._iterator.__anext__()
        return Signals(signum)
class TestRunner(abc.TestRunner):
    def __init__(self, **options: Any) -> None:
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        ...

    async def _run_tests_and_fixtures(self) -> None:
        self._send_stream, receive_stream = create_memory_object_stream(1)
        with receive_stream:
            async for coro, outcome_holder in receive_stream:
                try:
                    retval = await coro
                except BaseException as exc:
                    outcome_holder.append(Error(exc))
                else:
                    outcome_holder.append(Value(retval))
    def _main_task_finished(self, outcome: object) -> None:
        ...

    def _call_in_runner_task(
        self,
        func: Callable[P, Awaitable[T_Retval]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T_Retval:
        ...

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

class TrioTaskInfo(TaskInfo):
    def __init__(self, task: trio.lowlevel.Task):
        ...

    def has_pending_cancellation(self) -> bool:
        ...

class TrioBackend(AsyncBackend):
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
        await trio.lowlevel.checkpoint()
    @classmethod
    async def checkpoint_if_cancelled(cls) -> None:
        await trio.lowlevel.checkpoint_if_cancelled()
    @classmethod
    async def cancel_shielded_checkpoint(cls) -> None:
        await trio.lowlevel.cancel_shielded_checkpoint()
    @classmethod
    async def sleep(cls, delay: float) -> None:
        await trio.sleep(delay)
    @classmethod
    def create_cancel_scope(
        cls, *, deadline: float = math.inf, shield: bool = False
    ) -> abc.CancelScope:
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
    def create_lock(cls, *, fast_acquire: bool) -> Lock:
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
    def create_capacity_limiter(cls, total_tokens: float) -> CapacityLimiter:
        ...

    @classmethod
    async def run_sync_in_worker_thread(
        cls,
        func: Callable[[Unpack[PosArgsT]], T_Retval],
        args: tuple[Unpack[PosArgsT]],
        abandon_on_cancel: bool = False,
        limiter: abc.CapacityLimiter | None = None,
    ) -> T_Retval:
        def wrapper() -> T_Retval:
            ...

        token = TrioBackend.current_token()
        return await run_sync(
            wrapper,
            abandon_on_cancel=abandon_on_cancel,
            limiter=cast(trio.CapacityLimiter, limiter),
        )
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
        def convert_item(item: StrOrBytesPath) -> str:
            ...

        if isinstance(command, (str, bytes, PathLike)):
            process = await trio.lowlevel.open_process(
                convert_item(command),
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                shell=True,
                **kwargs,
            )
        else:
            process = await trio.lowlevel.open_process(
                [convert_item(item) for item in command],
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                shell=False,
                **kwargs,
            )
        stdin_stream = SendStreamWrapper(process.stdin) if process.stdin else None
        stdout_stream = ReceiveStreamWrapper(process.stdout) if process.stdout else None
        stderr_stream = ReceiveStreamWrapper(process.stderr) if process.stderr else None
        return Process(process, stdin_stream, stdout_stream, stderr_stream)
    @classmethod
    def setup_process_pool_exit_at_shutdown(cls, workers: set[abc.Process]) -> None:
        ...

    @classmethod
    async def connect_tcp(
        cls, host: str, port: int, local_address: IPSockAddrType | None = None
    ) -> SocketStream:
        family = socket.AF_INET6 if ":" in host else socket.AF_INET
        trio_socket = trio.socket.socket(family)
        trio_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        if local_address:
            await trio_socket.bind(local_address)
        try:
            await trio_socket.connect((host, port))
        except BaseException:
            trio_socket.close()
            raise
        return SocketStream(trio_socket)
    @classmethod
    async def connect_unix(cls, path: str | bytes) -> abc.UNIXSocketStream:
        trio_socket = trio.socket.socket(socket.AF_UNIX)
        try:
            await trio_socket.connect(path)
        except BaseException:
            trio_socket.close()
            raise
        return UNIXSocketStream(trio_socket)
    @classmethod
    def create_tcp_listener(cls, sock: socket.socket) -> abc.SocketListener:
        ...

    @classmethod
    def create_unix_listener(cls, sock: socket.socket) -> abc.SocketListener:
        ...

    @classmethod
    async def create_udp_socket(
        cls,
        family: socket.AddressFamily,
        local_address: IPSockAddrType | None,
        remote_address: IPSockAddrType | None,
        reuse_port: bool,
    ) -> UDPSocket | ConnectedUDPSocket:
        trio_socket = trio.socket.socket(family=family, type=socket.SOCK_DGRAM)
        if reuse_port:
            trio_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        if local_address:
            await trio_socket.bind(local_address)
        if remote_address:
            await trio_socket.connect(remote_address)
            return ConnectedUDPSocket(trio_socket)
        else:
            return UDPSocket(trio_socket)
    @classmethod
    @overload
    async def create_unix_datagram_socket(
        cls, raw_socket: socket.socket, remote_path: None
    ) -> abc.UNIXDatagramSocket: ...
    @classmethod
    @overload
    async def create_unix_datagram_socket(
        cls, raw_socket: socket.socket, remote_path: str | bytes
    ) -> abc.ConnectedUNIXDatagramSocket: ...
    @classmethod
    async def create_unix_datagram_socket(
        cls, raw_socket: socket.socket, remote_path: str | bytes | None
    ) -> abc.UNIXDatagramSocket | abc.ConnectedUNIXDatagramSocket:
        trio_socket = trio.socket.from_stdlib_socket(raw_socket)
        if remote_path:
            await trio_socket.connect(remote_path)
            return ConnectedUNIXDatagramSocket(trio_socket)
        else:
            return UNIXDatagramSocket(trio_socket)
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
        return await trio.socket.getaddrinfo(host, port, family, type, proto, flags)
    @classmethod
    async def getnameinfo(
        cls, sockaddr: IPSockAddrType, flags: int = 0
    ) -> tuple[str, str]:
        return await trio.socket.getnameinfo(sockaddr, flags)
    @classmethod
    async def wait_readable(cls, obj: FileDescriptorLike) -> None:
        try:
            await wait_readable(obj)
        except trio.ClosedResourceError as exc:
            raise ClosedResourceError().with_traceback(exc.__traceback__) from None
        except trio.BusyResourceError:
            raise BusyResourceError("reading from") from None
    @classmethod
    async def wait_writable(cls, obj: FileDescriptorLike) -> None:
        try:
            await wait_writable(obj)
        except trio.ClosedResourceError as exc:
            raise ClosedResourceError().with_traceback(exc.__traceback__) from None
        except trio.BusyResourceError:
            raise BusyResourceError("writing to") from None
    @classmethod
    def notify_closing(cls, obj: FileDescriptorLike) -> None:
        ...

    @classmethod
    async def wrap_listener_socket(cls, sock: socket.socket) -> abc.SocketListener:
        return TCPSocketListener(sock)
    @classmethod
    async def wrap_stream_socket(cls, sock: socket.socket) -> SocketStream:
        trio_sock = trio.socket.from_stdlib_socket(sock)
        return SocketStream(trio_sock)
    @classmethod
    async def wrap_unix_stream_socket(cls, sock: socket.socket) -> UNIXSocketStream:
        trio_sock = trio.socket.from_stdlib_socket(sock)
        return UNIXSocketStream(trio_sock)
    @classmethod
    async def wrap_udp_socket(cls, sock: socket.socket) -> UDPSocket:
        trio_sock = trio.socket.from_stdlib_socket(sock)
        return UDPSocket(trio_sock)
    @classmethod
    async def wrap_connected_udp_socket(cls, sock: socket.socket) -> ConnectedUDPSocket:
        trio_sock = trio.socket.from_stdlib_socket(sock)
        return ConnectedUDPSocket(trio_sock)
    @classmethod
    async def wrap_unix_datagram_socket(cls, sock: socket.socket) -> UNIXDatagramSocket:
        trio_sock = trio.socket.from_stdlib_socket(sock)
        return UNIXDatagramSocket(trio_sock)
    @classmethod
    async def wrap_connected_unix_datagram_socket(
        cls, sock: socket.socket
    ) -> ConnectedUNIXDatagramSocket:
        trio_sock = trio.socket.from_stdlib_socket(sock)
        return ConnectedUNIXDatagramSocket(trio_sock)
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
        from trio.testing import wait_all_tasks_blocked
        await wait_all_tasks_blocked()
    @classmethod
    def create_test_runner(cls, options: dict[str, Any]) -> TestRunner:
        ...

backend_class = TrioBackend
