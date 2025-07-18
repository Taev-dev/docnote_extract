"""This is a programmatically-vendored code sample
that has been stubbified (ie, function bodies removed). Do not modify
it directly; your changes will just be overwritten.

The original source is:
PkgSrcSpec(forge='github',
           repo_id='encode/httpx',
           pkg_name='httpx',
           offset_dest_root_dir=None,
           root_path='httpx',
           commit_hash='4fb9528c2f5ac000441c3634d297e77da23067cd',
           license_paths={'LICENSE.md'})

The license of the original project is included in the top level of
the vendored project directory.

To regenerate, see sidecars/docnote_extract_testpkg_factory. The
command is:
``uv run python -m docnote_extract_testpkg_factory``.

"""
from __future__ import annotations
import inspect
import warnings
from json import dumps as json_dumps
from typing import (
    Any,
    AsyncIterable,
    AsyncIterator,
    Iterable,
    Iterator,
    Mapping,
)
from urllib.parse import urlencode
from ._exceptions import StreamClosed, StreamConsumed
from ._multipart import MultipartStream
from ._types import (
    AsyncByteStream,
    RequestContent,
    RequestData,
    RequestFiles,
    ResponseContent,
    SyncByteStream,
)
from ._utils import peek_filelike_length, primitive_value_to_str
__all__ = ["ByteStream"]
class ByteStream(AsyncByteStream, SyncByteStream):
    def __init__(self, stream: bytes) -> None:
        ...

    def __iter__(self) -> Iterator[bytes]:
        ...

    async def __aiter__(self) -> AsyncIterator[bytes]:
        yield self._stream
class IteratorByteStream(SyncByteStream):
    CHUNK_SIZE = 65_536
    def __init__(self, stream: Iterable[bytes]) -> None:
        ...

    def __iter__(self) -> Iterator[bytes]:
        ...

class AsyncIteratorByteStream(AsyncByteStream):
    CHUNK_SIZE = 65_536
    def __init__(self, stream: AsyncIterable[bytes]) -> None:
        ...

    async def __aiter__(self) -> AsyncIterator[bytes]:
        if self._is_stream_consumed and self._is_generator:
            raise StreamConsumed()
        self._is_stream_consumed = True
        if hasattr(self._stream, "aread"):
            
            chunk = await self._stream.aread(self.CHUNK_SIZE)
            while chunk:
                yield chunk
                chunk = await self._stream.aread(self.CHUNK_SIZE)
        else:
            
            async for part in self._stream:
                yield part
class UnattachedStream(AsyncByteStream, SyncByteStream):
    """
    If a request or response is serialized using pickle, then it is no longer
    attached to a stream for I/O purposes. Any stream operations should result
    in `httpx.StreamClosed`.
    """
    def __iter__(self) -> Iterator[bytes]:
        ...

    async def __aiter__(self) -> AsyncIterator[bytes]:
        raise StreamClosed()
        yield b""  
def encode_content(
    content: str | bytes | Iterable[bytes] | AsyncIterable[bytes],
) -> tuple[dict[str, str], SyncByteStream | AsyncByteStream]:
    ...

def encode_urlencoded_data(
    data: RequestData,
) -> tuple[dict[str, str], ByteStream]:
    ...

def encode_multipart_data(
    data: RequestData, files: RequestFiles, boundary: bytes | None
) -> tuple[dict[str, str], MultipartStream]:
    ...

def encode_text(text: str) -> tuple[dict[str, str], ByteStream]:
    ...

def encode_html(html: str) -> tuple[dict[str, str], ByteStream]:
    ...

def encode_json(json: Any) -> tuple[dict[str, str], ByteStream]:
    ...

def encode_request(
    content: RequestContent | None = None,
    data: RequestData | None = None,
    files: RequestFiles | None = None,
    json: Any | None = None,
    boundary: bytes | None = None,
) -> tuple[dict[str, str], SyncByteStream | AsyncByteStream]:
    """
    Handles encoding the given `content`, `data`, `files`, and `json`,
    returning a two-tuple of (<headers>, <stream>).
    """
    ...

def encode_response(
    content: ResponseContent | None = None,
    text: str | None = None,
    html: str | None = None,
    json: Any | None = None,
) -> tuple[dict[str, str], SyncByteStream | AsyncByteStream]:
    """
    Handles encoding the given `content`, returning a two-tuple of
    (<headers>, <stream>).
    """
    ...

