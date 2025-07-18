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
import sys
from collections.abc import Awaitable, Callable, Generator
from concurrent.futures import Future
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    contextmanager,
)
from dataclasses import dataclass, field
from inspect import isawaitable
from threading import Lock, Thread, current_thread, get_ident
from types import TracebackType
from typing import (
    Any,
    Generic,
    TypeVar,
    cast,
    overload,
)
from ._core import _eventloop
from ._core._eventloop import get_async_backend, get_cancelled_exc_class, threadlocals
from ._core._synchronization import Event
from ._core._tasks import CancelScope, create_task_group
from .abc import AsyncBackend
from .abc._tasks import TaskStatus
if sys.version_info >= (3, 11):
    from typing import TypeVarTuple, Unpack
else:
    from typing_extensions import TypeVarTuple, Unpack
T_Retval = TypeVar("T_Retval")
T_co = TypeVar("T_co", covariant=True)
PosArgsT = TypeVarTuple("PosArgsT")
def run(
    func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval]], *args: Unpack[PosArgsT]
) -> T_Retval:
    """
    Call a coroutine function from a worker thread.
    :param func: a coroutine function
    :param args: positional arguments for the callable
    :return: the return value of the coroutine function
    """
    ...

def run_sync(
    func: Callable[[Unpack[PosArgsT]], T_Retval], *args: Unpack[PosArgsT]
) -> T_Retval:
    """
    Call a function in the event loop thread from a worker thread.
    :param func: a callable
    :param args: positional arguments for the callable
    :return: the return value of the callable
    """
    ...

class _BlockingAsyncContextManager(Generic[T_co], AbstractContextManager):
    _enter_future: Future[T_co]
    _exit_future: Future[bool | None]
    _exit_event: Event
    _exit_exc_info: tuple[
        type[BaseException] | None, BaseException | None, TracebackType | None
    ] = (None, None, None)
    def __init__(
        self, async_cm: AbstractAsyncContextManager[T_co], portal: BlockingPortal
    ):
        ...

    async def run_async_cm(self) -> bool | None:
        try:
            self._exit_event = Event()
            value = await self._async_cm.__aenter__()
        except BaseException as exc:
            self._enter_future.set_exception(exc)
            raise
        else:
            self._enter_future.set_result(value)
        try:
            await self._exit_event.wait()
        finally:
            result = await self._async_cm.__aexit__(*self._exit_exc_info)
        return result
    def __enter__(self) -> T_co:
        ...

    def __exit__(
        self,
        __exc_type: type[BaseException] | None,
        __exc_value: BaseException | None,
        __traceback: TracebackType | None,
    ) -> bool | None:
        ...

class _BlockingPortalTaskStatus(TaskStatus):
    def __init__(self, future: Future):
        ...

    def started(self, value: object = None) -> None:
        ...

class BlockingPortal:
    """An object that lets external threads run code in an asynchronous event loop."""
    def __new__(cls) -> BlockingPortal:
        return get_async_backend().create_blocking_portal()
    def __init__(self) -> None:
        self._event_loop_thread_id: int | None = get_ident()
        self._stop_event = Event()
        self._task_group = create_task_group()
        self._cancelled_exc_class = get_cancelled_exc_class()
    async def __aenter__(self) -> BlockingPortal:
        await self._task_group.__aenter__()
        return self
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        await self.stop()
        return await self._task_group.__aexit__(exc_type, exc_val, exc_tb)
    def _check_running(self) -> None:
        if self._event_loop_thread_id is None:
            raise RuntimeError("This portal is not running")
        if self._event_loop_thread_id == get_ident():
            raise RuntimeError(
                "This method cannot be called from the event loop thread"
            )
    async def sleep_until_stopped(self) -> None:
        """Sleep until :meth:`stop` is called."""
        await self._stop_event.wait()
    async def stop(self, cancel_remaining: bool = False) -> None:
        """
        Signal the portal to shut down.
        This marks the portal as no longer accepting new calls and exits from
        :meth:`sleep_until_stopped`.
        :param cancel_remaining: ``True`` to cancel all the remaining tasks, ``False``
            to let them finish before returning
        """
        self._event_loop_thread_id = None
        self._stop_event.set()
        if cancel_remaining:
            self._task_group.cancel_scope.cancel()
    async def _call_func(
        self,
        func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval] | T_Retval],
        args: tuple[Unpack[PosArgsT]],
        kwargs: dict[str, Any],
        future: Future[T_Retval],
    ) -> None:
        def callback(f: Future[T_Retval]) -> None:
            ...

        try:
            retval_or_awaitable = func(*args, **kwargs)
            if isawaitable(retval_or_awaitable):
                with CancelScope() as scope:
                    if future.cancelled():
                        scope.cancel()
                    else:
                        future.add_done_callback(callback)
                    retval = await retval_or_awaitable
            else:
                retval = retval_or_awaitable
        except self._cancelled_exc_class:
            future.cancel()
            future.set_running_or_notify_cancel()
        except BaseException as exc:
            if not future.cancelled():
                future.set_exception(exc)
            if not isinstance(exc, Exception):
                raise
        else:
            if not future.cancelled():
                future.set_result(retval)
        finally:
            scope = None  
    def _spawn_task_from_thread(
        self,
        func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval] | T_Retval],
        args: tuple[Unpack[PosArgsT]],
        kwargs: dict[str, Any],
        name: object,
        future: Future[T_Retval],
    ) -> None:
        """
        Spawn a new task using the given callable.
        Implementers must ensure that the future is resolved when the task finishes.
        :param func: a callable
        :param args: positional arguments to be passed to the callable
        :param kwargs: keyword arguments to be passed to the callable
        :param name: name of the task (will be coerced to a string if not ``None``)
        :param future: a future that will resolve to the return value of the callable,
            or the exception raised during its execution
        """
        ...

    @overload
    def call(
        self,
        func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval]],
        *args: Unpack[PosArgsT],
    ) -> T_Retval: ...
    @overload
    def call(
        self, func: Callable[[Unpack[PosArgsT]], T_Retval], *args: Unpack[PosArgsT]
    ) -> T_Retval: ...
    def call(
        self,
        func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval] | T_Retval],
        *args: Unpack[PosArgsT],
    ) -> T_Retval:
        """
        Call the given function in the event loop thread.
        If the callable returns a coroutine object, it is awaited on.
        :param func: any callable
        :raises RuntimeError: if the portal is not running or if this method is called
            from within the event loop thread
        """
        ...

    @overload
    def start_task_soon(
        self,
        func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval]],
        *args: Unpack[PosArgsT],
        name: object = None,
    ) -> Future[T_Retval]: ...
    @overload
    def start_task_soon(
        self,
        func: Callable[[Unpack[PosArgsT]], T_Retval],
        *args: Unpack[PosArgsT],
        name: object = None,
    ) -> Future[T_Retval]: ...
    def start_task_soon(
        self,
        func: Callable[[Unpack[PosArgsT]], Awaitable[T_Retval] | T_Retval],
        *args: Unpack[PosArgsT],
        name: object = None,
    ) -> Future[T_Retval]:
        """
        Start a task in the portal's task group.
        The task will be run inside a cancel scope which can be cancelled by cancelling
        the returned future.
        :param func: the target function
        :param args: positional arguments passed to ``func``
        :param name: name of the task (will be coerced to a string if not ``None``)
        :return: a future that resolves with the return value of the callable if the
            task completes successfully, or with the exception raised in the task
        :raises RuntimeError: if the portal is not running or if this method is called
            from within the event loop thread
        :rtype: concurrent.futures.Future[T_Retval]
        .. versionadded:: 3.0
        """
        ...

    def start_task(
        self,
        func: Callable[..., Awaitable[T_Retval]],
        *args: object,
        name: object = None,
    ) -> tuple[Future[T_Retval], Any]:
        """
        Start a task in the portal's task group and wait until it signals for readiness.
        This method works the same way as :meth:`.abc.TaskGroup.start`.
        :param func: the target function
        :param args: positional arguments passed to ``func``
        :param name: name of the task (will be coerced to a string if not ``None``)
        :return: a tuple of (future, task_status_value) where the ``task_status_value``
            is the value passed to ``task_status.started()`` from within the target
            function
        :rtype: tuple[concurrent.futures.Future[T_Retval], Any]
        .. versionadded:: 3.0
        """
        ...

    def wrap_async_context_manager(
        self, cm: AbstractAsyncContextManager[T_co]
    ) -> AbstractContextManager[T_co]:
        """
        Wrap an async context manager as a synchronous context manager via this portal.
        Spawns a task that will call both ``__aenter__()`` and ``__aexit__()``, stopping
        in the middle until the synchronous context manager exits.
        :param cm: an asynchronous context manager
        :return: a synchronous context manager
        .. versionadded:: 2.1
        """
        ...

@dataclass
class BlockingPortalProvider:
    """
    A manager for a blocking portal. Used as a context manager. The first thread to
    enter this context manager causes a blocking portal to be started with the specific
    parameters, and the last thread to exit causes the portal to be shut down. Thus,
    there will be exactly one blocking portal running in this context as long as at
    least one thread has entered this context manager.
    The parameters are the same as for :func:`~anyio.run`.
    :param backend: name of the backend
    :param backend_options: backend options
    .. versionadded:: 4.4
    """
    backend: str = "asyncio"
    backend_options: dict[str, Any] | None = None
    _lock: Lock = field(init=False, default_factory=Lock)
    _leases: int = field(init=False, default=0)
    _portal: BlockingPortal = field(init=False)
    _portal_cm: AbstractContextManager[BlockingPortal] | None = field(
        init=False, default=None
    )
    def __enter__(self) -> BlockingPortal:
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        ...

@contextmanager
def start_blocking_portal(
    backend: str = "asyncio",
    backend_options: dict[str, Any] | None = None,
    *,
    name: str | None = None,
) -> Generator[BlockingPortal, Any, None]:
    """
    Start a new event loop in a new thread and run a blocking portal in its main task.
    The parameters are the same as for :func:`~anyio.run`.
    :param backend: name of the backend
    :param backend_options: backend options
    :param name: name of the thread
    :return: a context manager that yields a blocking portal
    .. versionchanged:: 3.0
        Usage as a context manager is now required.
    """
    ...

def check_cancelled() -> None:
    """
    Check if the cancel scope of the host task's running the current worker thread has
    been cancelled.
    If the host task's current cancel scope has indeed been cancelled, the
    backend-specific cancellation exception will be raised.
    :raises RuntimeError: if the current thread was not spawned by
        :func:`.to_thread.run_sync`
    """
    ...

