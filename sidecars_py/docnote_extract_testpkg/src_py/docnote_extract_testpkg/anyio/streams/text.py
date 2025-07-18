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
import codecs
import sys
from collections.abc import Callable, Mapping
from dataclasses import InitVar, dataclass, field
from typing import Any
from ..abc import (
    AnyByteReceiveStream,
    AnyByteSendStream,
    AnyByteStream,
    AnyByteStreamConnectable,
    ObjectReceiveStream,
    ObjectSendStream,
    ObjectStream,
    ObjectStreamConnectable,
)
if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override
@dataclass(eq=False)
class TextReceiveStream(ObjectReceiveStream[str]):
    """
    Stream wrapper that decodes bytes to strings using the given encoding.
    Decoding is done using :class:`~codecs.IncrementalDecoder` which returns any
    completely received unicode characters as soon as they come in.
    :param transport_stream: any bytes-based receive stream
    :param encoding: character encoding to use for decoding bytes to strings (defaults
        to ``utf-8``)
    :param errors: handling scheme for decoding errors (defaults to ``strict``; see the
        `codecs module documentation`_ for a comprehensive list of options)
    .. _codecs module documentation:
        https://docs.python.org/3/library/codecs.html
    """
    transport_stream: AnyByteReceiveStream
    encoding: InitVar[str] = "utf-8"
    errors: InitVar[str] = "strict"
    _decoder: codecs.IncrementalDecoder = field(init=False)
    def __post_init__(self, encoding: str, errors: str) -> None:
        ...

    async def receive(self) -> str:
        while True:
            chunk = await self.transport_stream.receive()
            decoded = self._decoder.decode(chunk)
            if decoded:
                return decoded
    async def aclose(self) -> None:
        await self.transport_stream.aclose()
        self._decoder.reset()
    @property
    def extra_attributes(self) -> Mapping[Any, Callable[[], Any]]:
        ...

@dataclass(eq=False)
class TextSendStream(ObjectSendStream[str]):
    """
    Sends strings to the wrapped stream as bytes using the given encoding.
    :param AnyByteSendStream transport_stream: any bytes-based send stream
    :param str encoding: character encoding to use for encoding strings to bytes
        (defaults to ``utf-8``)
    :param str errors: handling scheme for encoding errors (defaults to ``strict``; see
        the `codecs module documentation`_ for a comprehensive list of options)
    .. _codecs module documentation:
        https://docs.python.org/3/library/codecs.html
    """
    transport_stream: AnyByteSendStream
    encoding: InitVar[str] = "utf-8"
    errors: str = "strict"
    _encoder: Callable[..., tuple[bytes, int]] = field(init=False)
    def __post_init__(self, encoding: str) -> None:
        ...

    async def send(self, item: str) -> None:
        encoded = self._encoder(item, self.errors)[0]
        await self.transport_stream.send(encoded)
    async def aclose(self) -> None:
        await self.transport_stream.aclose()
    @property
    def extra_attributes(self) -> Mapping[Any, Callable[[], Any]]:
        ...

@dataclass(eq=False)
class TextStream(ObjectStream[str]):
    """
    A bidirectional stream that decodes bytes to strings on receive and encodes strings
    to bytes on send.
    Extra attributes will be provided from both streams, with the receive stream
    providing the values in case of a conflict.
    :param AnyByteStream transport_stream: any bytes-based stream
    :param str encoding: character encoding to use for encoding/decoding strings to/from
        bytes (defaults to ``utf-8``)
    :param str errors: handling scheme for encoding errors (defaults to ``strict``; see
        the `codecs module documentation`_ for a comprehensive list of options)
    .. _codecs module documentation:
        https://docs.python.org/3/library/codecs.html
    """
    transport_stream: AnyByteStream
    encoding: InitVar[str] = "utf-8"
    errors: InitVar[str] = "strict"
    _receive_stream: TextReceiveStream = field(init=False)
    _send_stream: TextSendStream = field(init=False)
    def __post_init__(self, encoding: str, errors: str) -> None:
        ...

    async def receive(self) -> str:
        return await self._receive_stream.receive()
    async def send(self, item: str) -> None:
        await self._send_stream.send(item)
    async def send_eof(self) -> None:
        await self.transport_stream.send_eof()
    async def aclose(self) -> None:
        await self._send_stream.aclose()
        await self._receive_stream.aclose()
    @property
    def extra_attributes(self) -> Mapping[Any, Callable[[], Any]]:
        ...

class TextConnectable(ObjectStreamConnectable[str]):
    def __init__(self, connectable: AnyByteStreamConnectable):
        """
        :param connectable: the bytestream endpoint to wrap
        """
        ...

    @override
    async def connect(self) -> TextStream:
        stream = await self.connectable.connect()
        return TextStream(stream)
