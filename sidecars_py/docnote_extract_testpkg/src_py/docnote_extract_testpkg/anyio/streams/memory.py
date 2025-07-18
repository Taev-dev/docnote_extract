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
import warnings
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from types import TracebackType
from typing import Generic, NamedTuple, TypeVar
from .. import (
    BrokenResourceError,
    ClosedResourceError,
    EndOfStream,
    WouldBlock,
)
from .._core._testing import TaskInfo, get_current_task
from ..abc import Event, ObjectReceiveStream, ObjectSendStream
from ..lowlevel import checkpoint
T_Item = TypeVar("T_Item")
T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)
class MemoryObjectStreamStatistics(NamedTuple):
    current_buffer_used: int  
    
    max_buffer_size: float
    open_send_streams: int  
    open_receive_streams: int  
    
    tasks_waiting_send: int
    
    tasks_waiting_receive: int
@dataclass(eq=False)
class MemoryObjectItemReceiver(Generic[T_Item]):
    task_info: TaskInfo = field(init=False, default_factory=get_current_task)
    item: T_Item = field(init=False)
    def __repr__(self) -> str:
        ...

@dataclass(eq=False)
class MemoryObjectStreamState(Generic[T_Item]):
    max_buffer_size: float = field()
    buffer: deque[T_Item] = field(init=False, default_factory=deque)
    open_send_channels: int = field(init=False, default=0)
    open_receive_channels: int = field(init=False, default=0)
    waiting_receivers: OrderedDict[Event, MemoryObjectItemReceiver[T_Item]] = field(
        init=False, default_factory=OrderedDict
    )
    waiting_senders: OrderedDict[Event, T_Item] = field(
        init=False, default_factory=OrderedDict
    )
    def statistics(self) -> MemoryObjectStreamStatistics:
        ...

@dataclass(eq=False)
class MemoryObjectReceiveStream(Generic[T_co], ObjectReceiveStream[T_co]):
    _state: MemoryObjectStreamState[T_co]
    _closed: bool = field(init=False, default=False)
    def __post_init__(self) -> None:
        ...

    def receive_nowait(self) -> T_co:
        """
        Receive the next item if it can be done without waiting.
        :return: the received item
        :raises ~anyio.ClosedResourceError: if this send stream has been closed
        :raises ~anyio.EndOfStream: if the buffer is empty and this stream has been
            closed from the sending end
        :raises ~anyio.WouldBlock: if there are no items in the buffer and no tasks
            waiting to send
        """
        ...

    async def receive(self) -> T_co:
        await checkpoint()
        try:
            return self.receive_nowait()
        except WouldBlock:
            
            receive_event = Event()
            receiver = MemoryObjectItemReceiver[T_co]()
            self._state.waiting_receivers[receive_event] = receiver
            try:
                await receive_event.wait()
            finally:
                self._state.waiting_receivers.pop(receive_event, None)
            try:
                return receiver.item
            except AttributeError:
                raise EndOfStream from None
    def clone(self) -> MemoryObjectReceiveStream[T_co]:
        """
        Create a clone of this receive stream.
        Each clone can be closed separately. Only when all clones have been closed will
        the receiving end of the memory stream be considered closed by the sending ends.
        :return: the cloned stream
        """
        ...

    def close(self) -> None:
        """
        Close the stream.
        This works the exact same way as :meth:`aclose`, but is provided as a special
        case for the benefit of synchronous callbacks.
        """
        ...

    async def aclose(self) -> None:
        self.close()
    def statistics(self) -> MemoryObjectStreamStatistics:
        """
        Return statistics about the current state of this stream.
        .. versionadded:: 3.0
        """
        ...

    def __enter__(self) -> MemoryObjectReceiveStream[T_co]:
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        ...

    def __del__(self) -> None:
        ...

@dataclass(eq=False)
class MemoryObjectSendStream(Generic[T_contra], ObjectSendStream[T_contra]):
    _state: MemoryObjectStreamState[T_contra]
    _closed: bool = field(init=False, default=False)
    def __post_init__(self) -> None:
        ...

    def send_nowait(self, item: T_contra) -> None:
        """
        Send an item immediately if it can be done without waiting.
        :param item: the item to send
        :raises ~anyio.ClosedResourceError: if this send stream has been closed
        :raises ~anyio.BrokenResourceError: if the stream has been closed from the
            receiving end
        :raises ~anyio.WouldBlock: if the buffer is full and there are no tasks waiting
            to receive
        """
        ...

    async def send(self, item: T_contra) -> None:
        """
        Send an item to the stream.
        If the buffer is full, this method blocks until there is again room in the
        buffer or the item can be sent directly to a receiver.
        :param item: the item to send
        :raises ~anyio.ClosedResourceError: if this send stream has been closed
        :raises ~anyio.BrokenResourceError: if the stream has been closed from the
            receiving end
        """
        await checkpoint()
        try:
            self.send_nowait(item)
        except WouldBlock:
            
            send_event = Event()
            self._state.waiting_senders[send_event] = item
            try:
                await send_event.wait()
            except BaseException:
                self._state.waiting_senders.pop(send_event, None)
                raise
            if send_event in self._state.waiting_senders:
                del self._state.waiting_senders[send_event]
                raise BrokenResourceError from None
    def clone(self) -> MemoryObjectSendStream[T_contra]:
        """
        Create a clone of this send stream.
        Each clone can be closed separately. Only when all clones have been closed will
        the sending end of the memory stream be considered closed by the receiving ends.
        :return: the cloned stream
        """
        ...

    def close(self) -> None:
        """
        Close the stream.
        This works the exact same way as :meth:`aclose`, but is provided as a special
        case for the benefit of synchronous callbacks.
        """
        ...

    async def aclose(self) -> None:
        self.close()
    def statistics(self) -> MemoryObjectStreamStatistics:
        """
        Return statistics about the current state of this stream.
        .. versionadded:: 3.0
        """
        ...

    def __enter__(self) -> MemoryObjectSendStream[T_contra]:
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        ...

    def __del__(self) -> None:
        ...

