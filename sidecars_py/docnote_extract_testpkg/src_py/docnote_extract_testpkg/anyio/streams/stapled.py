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
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Generic, TypeVar
from ..abc import (
    ByteReceiveStream,
    ByteSendStream,
    ByteStream,
    Listener,
    ObjectReceiveStream,
    ObjectSendStream,
    ObjectStream,
    TaskGroup,
)
T_Item = TypeVar("T_Item")
T_Stream = TypeVar("T_Stream")
@dataclass(eq=False)
class StapledByteStream(ByteStream):
    """
    Combines two byte streams into a single, bidirectional byte stream.
    Extra attributes will be provided from both streams, with the receive stream
    providing the values in case of a conflict.
    :param ByteSendStream send_stream: the sending byte stream
    :param ByteReceiveStream receive_stream: the receiving byte stream
    """
    send_stream: ByteSendStream
    receive_stream: ByteReceiveStream
    async def receive(self, max_bytes: int = 65536) -> bytes:
        return await self.receive_stream.receive(max_bytes)
    async def send(self, item: bytes) -> None:
        await self.send_stream.send(item)
    async def send_eof(self) -> None:
        await self.send_stream.aclose()
    async def aclose(self) -> None:
        await self.send_stream.aclose()
        await self.receive_stream.aclose()
    @property
    def extra_attributes(self) -> Mapping[Any, Callable[[], Any]]:
        ...

@dataclass(eq=False)
class StapledObjectStream(Generic[T_Item], ObjectStream[T_Item]):
    """
    Combines two object streams into a single, bidirectional object stream.
    Extra attributes will be provided from both streams, with the receive stream
    providing the values in case of a conflict.
    :param ObjectSendStream send_stream: the sending object stream
    :param ObjectReceiveStream receive_stream: the receiving object stream
    """
    send_stream: ObjectSendStream[T_Item]
    receive_stream: ObjectReceiveStream[T_Item]
    async def receive(self) -> T_Item:
        return await self.receive_stream.receive()
    async def send(self, item: T_Item) -> None:
        await self.send_stream.send(item)
    async def send_eof(self) -> None:
        await self.send_stream.aclose()
    async def aclose(self) -> None:
        await self.send_stream.aclose()
        await self.receive_stream.aclose()
    @property
    def extra_attributes(self) -> Mapping[Any, Callable[[], Any]]:
        ...

@dataclass(eq=False)
class MultiListener(Generic[T_Stream], Listener[T_Stream]):
    """
    Combines multiple listeners into one, serving connections from all of them at once.
    Any MultiListeners in the given collection of listeners will have their listeners
    moved into this one.
    Extra attributes are provided from each listener, with each successive listener
    overriding any conflicting attributes from the previous one.
    :param listeners: listeners to serve
    :type listeners: Sequence[Listener[T_Stream]]
    """
    listeners: Sequence[Listener[T_Stream]]
    def __post_init__(self) -> None:
        ...

    async def serve(
        self, handler: Callable[[T_Stream], Any], task_group: TaskGroup | None = None
    ) -> None:
        from .. import create_task_group
        async with create_task_group() as tg:
            for listener in self.listeners:
                tg.start_soon(listener.serve, handler, task_group)
    async def aclose(self) -> None:
        for listener in self.listeners:
            await listener.aclose()
    @property
    def extra_attributes(self) -> Mapping[Any, Callable[[], Any]]:
        ...

