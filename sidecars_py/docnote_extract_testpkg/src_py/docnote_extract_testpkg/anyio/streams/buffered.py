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
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any
from .. import ClosedResourceError, DelimiterNotFound, EndOfStream, IncompleteRead
from ..abc import (
    AnyByteReceiveStream,
    AnyByteStream,
    AnyByteStreamConnectable,
    ByteReceiveStream,
    ByteStream,
    ByteStreamConnectable,
)
if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override
@dataclass(eq=False)
class BufferedByteReceiveStream(ByteReceiveStream):
    """
    Wraps any bytes-based receive stream and uses a buffer to provide sophisticated
    receiving capabilities in the form of a byte stream.
    """
    receive_stream: AnyByteReceiveStream
    _buffer: bytearray = field(init=False, default_factory=bytearray)
    _closed: bool = field(init=False, default=False)
    async def aclose(self) -> None:
        await self.receive_stream.aclose()
        self._closed = True
    @property
    def buffer(self) -> bytes:
        """The bytes currently in the buffer."""
        return bytes(self._buffer)
    @property
    def extra_attributes(self) -> Mapping[Any, Callable[[], Any]]:
        return self.receive_stream.extra_attributes
    async def receive(self, max_bytes: int = 65536) -> bytes:
        if self._closed:
            raise ClosedResourceError
        if self._buffer:
            chunk = bytes(self._buffer[:max_bytes])
            del self._buffer[:max_bytes]
            return chunk
        elif isinstance(self.receive_stream, ByteReceiveStream):
            return await self.receive_stream.receive(max_bytes)
        else:
            chunk = await self.receive_stream.receive()
            if len(chunk) > max_bytes:
                self._buffer.extend(chunk[max_bytes:])
                return chunk[:max_bytes]
            else:
                return chunk
    async def receive_exactly(self, nbytes: int) -> bytes:
        """
        """
        while True:
            remaining = nbytes - len(self._buffer)
            if remaining <= 0:
                retval = self._buffer[:nbytes]
                del self._buffer[:nbytes]
                return bytes(retval)
            try:
                if isinstance(self.receive_stream, ByteReceiveStream):
                    chunk = await self.receive_stream.receive(remaining)
                else:
                    chunk = await self.receive_stream.receive()
            except EndOfStream as exc:
                raise IncompleteRead from exc
            self._buffer.extend(chunk)
    async def receive_until(self, delimiter: bytes, max_bytes: int) -> bytes:
        """
        """
        delimiter_size = len(delimiter)
        offset = 0
        while True:
            index = self._buffer.find(delimiter, offset)
            if index >= 0:
                found = self._buffer[:index]
                del self._buffer[: index + len(delimiter) :]
                return bytes(found)
            if len(self._buffer) >= max_bytes:
                raise DelimiterNotFound(max_bytes)
            try:
                data = await self.receive_stream.receive()
            except EndOfStream as exc:
                raise IncompleteRead from exc
            offset = max(len(self._buffer) - delimiter_size + 1, 0)
            self._buffer.extend(data)
class BufferedByteStream(BufferedByteReceiveStream, ByteStream):
    """
        ...

    A full-duplex variant of :class:`BufferedByteReceiveStream`. All writes are passed
    through to the wrapped stream as-is.
    """
    def __init__(self, stream: AnyByteStream):
        """
        :param stream: the stream to be wrapped
        """
        super().__init__(stream)
        self._stream = stream
    @override
    async def send_eof(self) -> None:
        await self._stream.send_eof()
    @override
    async def send(self, item: bytes) -> None:
        await self._stream.send(item)
class BufferedConnectable(ByteStreamConnectable):
    def __init__(self, connectable: AnyByteStreamConnectable):
        """
        :param connectable: the connectable to wrap
        """
        self.connectable = connectable
    @override
    async def connect(self) -> BufferedByteStream:
        stream = await self.connectable.connect()
        return BufferedByteStream(stream)
