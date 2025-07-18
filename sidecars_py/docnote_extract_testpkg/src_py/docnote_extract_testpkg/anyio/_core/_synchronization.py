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
import math
from collections import deque
from dataclasses import dataclass
from types import TracebackType
from sniffio import AsyncLibraryNotFoundError
from ..lowlevel import checkpoint
from ._eventloop import get_async_backend
from ._exceptions import BusyResourceError
from ._tasks import CancelScope
from ._testing import TaskInfo, get_current_task
@dataclass(frozen=True)
class EventStatistics:
    """
    :ivar int tasks_waiting: number of tasks waiting on :meth:`~.Event.wait`
    """
    tasks_waiting: int
@dataclass(frozen=True)
class CapacityLimiterStatistics:
    """
    :ivar int borrowed_tokens: number of tokens currently borrowed by tasks
    :ivar float total_tokens: total number of available tokens
    :ivar tuple borrowers: tasks or other objects currently holding tokens borrowed from
        this limiter
    :ivar int tasks_waiting: number of tasks waiting on
        :meth:`~.CapacityLimiter.acquire` or
        :meth:`~.CapacityLimiter.acquire_on_behalf_of`
    """
    borrowed_tokens: int
    total_tokens: float
    borrowers: tuple[object, ...]
    tasks_waiting: int
@dataclass(frozen=True)
class LockStatistics:
    """
    :ivar bool locked: flag indicating if this lock is locked or not
    :ivar ~anyio.TaskInfo owner: task currently holding the lock (or ``None`` if the
        lock is not held by any task)
    :ivar int tasks_waiting: number of tasks waiting on :meth:`~.Lock.acquire`
    """
    locked: bool
    owner: TaskInfo | None
    tasks_waiting: int
@dataclass(frozen=True)
class ConditionStatistics:
    """
    :ivar int tasks_waiting: number of tasks blocked on :meth:`~.Condition.wait`
    :ivar ~anyio.LockStatistics lock_statistics: statistics of the underlying
        :class:`~.Lock`
    """
    tasks_waiting: int
    lock_statistics: LockStatistics
@dataclass(frozen=True)
class SemaphoreStatistics:
    """
    :ivar int tasks_waiting: number of tasks waiting on :meth:`~.Semaphore.acquire`
    """
    tasks_waiting: int
class Event:
    def __new__(cls) -> Event:
        ...

    def set(self) -> None:
        """Set the flag, notifying all listeners."""
        raise NotImplementedError
    def is_set(self) -> bool:
        """Return ``True`` if the flag is set, ``False`` if not."""
        ...

    async def wait(self) -> None:
        """
        Wait until the flag has been set.
        If the flag has already been set when this method is called, it returns
        immediately.
        """
        raise NotImplementedError
    def statistics(self) -> EventStatistics:
        """Return statistics about the current state of this event."""
        raise NotImplementedError
class EventAdapter(Event):
    _internal_event: Event | None = None
    _is_set: bool = False
    def __new__(cls) -> EventAdapter:
        return object.__new__(cls)
    @property
    def _event(self) -> Event:
        if self._internal_event is None:
            self._internal_event = get_async_backend().create_event()
            if self._is_set:
                self._internal_event.set()
        return self._internal_event
    def set(self) -> None:
        if self._internal_event is None:
            self._is_set = True
        else:
            self._event.set()
    def is_set(self) -> bool:
        if self._internal_event is None:
            return self._is_set
        return self._internal_event.is_set()
    async def wait(self) -> None:
        await self._event.wait()
    def statistics(self) -> EventStatistics:
        if self._internal_event is None:
            return EventStatistics(tasks_waiting=0)
        return self._internal_event.statistics()
class Lock:
    def __new__(cls, *, fast_acquire: bool = False) -> Lock:
        try:
            return get_async_backend().create_lock(fast_acquire=fast_acquire)
        except AsyncLibraryNotFoundError:
            return LockAdapter(fast_acquire=fast_acquire)
    async def __aenter__(self) -> None:
        await self.acquire()
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.release()
    async def acquire(self) -> None:
        """Acquire the lock."""
        ...

    def acquire_nowait(self) -> None:
        """
        Acquire the lock, without blocking.
        :raises ~anyio.WouldBlock: if the operation would block
        """
        ...

    def release(self) -> None:
        """Release the lock."""
        raise NotImplementedError
    def locked(self) -> bool:
        """Return True if the lock is currently held."""
        ...

    def statistics(self) -> LockStatistics:
        """
        Return statistics about the current state of this lock.
        .. versionadded:: 3.0
        """
        ...

class LockAdapter(Lock):
    _internal_lock: Lock | None = None
    def __new__(cls, *, fast_acquire: bool = False) -> LockAdapter:
        ...

    def __init__(self, *, fast_acquire: bool = False):
        ...

    @property
    def _lock(self) -> Lock:
        ...

    async def __aenter__(self) -> None:
        await self._lock.acquire()
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._internal_lock is not None:
            self._internal_lock.release()
    async def acquire(self) -> None:
        """Acquire the lock."""
        await self._lock.acquire()
    def acquire_nowait(self) -> None:
        """
        Acquire the lock, without blocking.
        :raises ~anyio.WouldBlock: if the operation would block
        """
        ...

    def release(self) -> None:
        """Release the lock."""
        self._lock.release()
    def locked(self) -> bool:
        """Return True if the lock is currently held."""
        ...

    def statistics(self) -> LockStatistics:
        """
        Return statistics about the current state of this lock.
        .. versionadded:: 3.0
        """
        ...

class Condition:
    _owner_task: TaskInfo | None = None
    def __init__(self, lock: Lock | None = None):
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
    def _check_acquired(self) -> None:
        ...

    async def acquire(self) -> None:
        """Acquire the underlying lock."""
        await self._lock.acquire()
        self._owner_task = get_current_task()
    def acquire_nowait(self) -> None:
        """
        Acquire the underlying lock, without blocking.
        :raises ~anyio.WouldBlock: if the operation would block
        """
        ...

    def release(self) -> None:
        """Release the underlying lock."""
        self._lock.release()
    def locked(self) -> bool:
        """Return True if the lock is set."""
        ...

    def notify(self, n: int = 1) -> None:
        """Notify exactly n listeners."""
        self._check_acquired()
        for _ in range(n):
            try:
                event = self._waiters.popleft()
            except IndexError:
                break
            event.set()
    def notify_all(self) -> None:
        """Notify all the listeners."""
        ...

    async def wait(self) -> None:
        """Wait for a notification."""
        await checkpoint()
        event = Event()
        self._waiters.append(event)
        self.release()
        try:
            await event.wait()
        except BaseException:
            if not event.is_set():
                self._waiters.remove(event)
            raise
        finally:
            with CancelScope(shield=True):
                await self.acquire()
    def statistics(self) -> ConditionStatistics:
        """
        Return statistics about the current state of this condition.
        .. versionadded:: 3.0
        """
        ...

class Semaphore:
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

    async def __aenter__(self) -> Semaphore:
        await self.acquire()
        return self
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.release()
    async def acquire(self) -> None:
        """Decrement the semaphore value, blocking if necessary."""
        raise NotImplementedError
    def acquire_nowait(self) -> None:
        """
        Acquire the underlying lock, without blocking.
        :raises ~anyio.WouldBlock: if the operation would block
        """
        ...

    def release(self) -> None:
        """Increment the semaphore value."""
        raise NotImplementedError
    @property
    def value(self) -> int:
        """The current value of the semaphore."""
        ...

    @property
    def max_value(self) -> int | None:
        """The maximum value of the semaphore."""
        raise NotImplementedError
    def statistics(self) -> SemaphoreStatistics:
        """
        ...

class SemaphoreAdapter(Semaphore):
    _internal_semaphore: Semaphore | None = None
    def __new__(
        cls,
        initial_value: int,
        *,
        max_value: int | None = None,
        fast_acquire: bool = False,
    ) -> SemaphoreAdapter:
        ...

    def __init__(
        self,
        initial_value: int,
        *,
        max_value: int | None = None,
        fast_acquire: bool = False,
    ) -> None:
        ...

    @property
    def _semaphore(self) -> Semaphore:
        ...

    async def acquire(self) -> None:
        await self._semaphore.acquire()
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

class CapacityLimiter:
    def __new__(cls, total_tokens: float) -> CapacityLimiter:
        ...

    async def __aenter__(self) -> None:
        raise NotImplementedError
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        raise NotImplementedError
    @property
    def total_tokens(self) -> float:
        """
        The total number of tokens available for borrowing.
        This is a read-write property. If the total number of tokens is increased, the
        proportionate number of tasks waiting on this limiter will be granted their
        tokens.
        .. versionchanged:: 3.0
            The property is now writable.
        """
        ...

    @total_tokens.setter
    def total_tokens(self, value: float) -> None:
        ...

    @property
    def borrowed_tokens(self) -> int:
        """The number of tokens that have currently been borrowed."""
        raise NotImplementedError
    @property
    def available_tokens(self) -> float:
        """The number of tokens currently available to be borrowed"""
        ...

    def acquire_nowait(self) -> None:
        """
        Acquire a token for the current task without waiting for one to become
        available.
        :raises ~anyio.WouldBlock: if there are no tokens available for borrowing
        """
        ...

    def acquire_on_behalf_of_nowait(self, borrower: object) -> None:
        """
        Acquire a token without waiting for one to become available.
        :param borrower: the entity borrowing a token
        :raises ~anyio.WouldBlock: if there are no tokens available for borrowing
        """
        ...

    async def acquire(self) -> None:
        """
        Acquire a token for the current task, waiting if necessary for one to become
        available.
        """
        raise NotImplementedError
    async def acquire_on_behalf_of(self, borrower: object) -> None:
        """
        Acquire a token, waiting if necessary for one to become available.
        :param borrower: the entity borrowing a token
        """
        raise NotImplementedError
    def release(self) -> None:
        """
        Release the token held by the current task.
        :raises RuntimeError: if the current task has not borrowed a token from this
            limiter.
        """
        ...

    def release_on_behalf_of(self, borrower: object) -> None:
        """
        Release the token held by the given borrower.
        :raises RuntimeError: if the borrower has not borrowed a token from this
            limiter.
        """
        ...

    def statistics(self) -> CapacityLimiterStatistics:
        """
        Return statistics about the current state of this limiter.
        .. versionadded:: 3.0
        """
        ...

class CapacityLimiterAdapter(CapacityLimiter):
    _internal_limiter: CapacityLimiter | None = None
    def __new__(cls, total_tokens: float) -> CapacityLimiterAdapter:
        ...

    def __init__(self, total_tokens: float) -> None:
        ...

    @property
    def _limiter(self) -> CapacityLimiter:
        ...

    async def __aenter__(self) -> None:
        await self._limiter.__aenter__()
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return await self._limiter.__aexit__(exc_type, exc_val, exc_tb)
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
        await self._limiter.acquire()
    async def acquire_on_behalf_of(self, borrower: object) -> None:
        await self._limiter.acquire_on_behalf_of(borrower)
    def release(self) -> None:
        ...

    def release_on_behalf_of(self, borrower: object) -> None:
        ...

    def statistics(self) -> CapacityLimiterStatistics:
        ...

class ResourceGuard:
    """
    A context manager for ensuring that a resource is only used by a single task at a
    time.
    Entering this context manager while the previous has not exited it yet will trigger
    :exc:`BusyResourceError`.
    :param action: the action to guard against (visible in the :exc:`BusyResourceError`
        when triggered, e.g. "Another task is already {action} this resource")
    .. versionadded:: 4.1
    """
    __slots__ = "action", "_guarded"
    def __init__(self, action: str = "using"):
        ...

    def __enter__(self) -> None:
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        ...

