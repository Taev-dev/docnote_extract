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
import codecs
import datetime
import email.message
import json as jsonlib
import re
import typing
import urllib.request
from collections.abc import Mapping
from http.cookiejar import Cookie, CookieJar
from ._content import ByteStream, UnattachedStream, encode_request, encode_response
from ._decoders import (
    SUPPORTED_DECODERS,
    ByteChunker,
    ContentDecoder,
    IdentityDecoder,
    LineDecoder,
    MultiDecoder,
    TextChunker,
    TextDecoder,
)
from ._exceptions import (
    CookieConflict,
    HTTPStatusError,
    RequestNotRead,
    ResponseNotRead,
    StreamClosed,
    StreamConsumed,
    request_context,
)
from ._multipart import get_multipart_boundary_from_content_type
from ._status_codes import codes
from ._types import (
    AsyncByteStream,
    CookieTypes,
    HeaderTypes,
    QueryParamTypes,
    RequestContent,
    RequestData,
    RequestExtensions,
    RequestFiles,
    ResponseContent,
    ResponseExtensions,
    SyncByteStream,
)
from ._urls import URL
from ._utils import to_bytes_or_str, to_str
__all__ = ["Cookies", "Headers", "Request", "Response"]
SENSITIVE_HEADERS = {"authorization", "proxy-authorization"}
def _is_known_encoding(encoding: str) -> bool:
    """
    Return `True` if `encoding` is a known codec.
    """
    ...

def _normalize_header_key(key: str | bytes, encoding: str | None = None) -> bytes:
    """
    Coerce str/bytes into a strictly byte-wise HTTP header key.
    """
    ...

def _normalize_header_value(value: str | bytes, encoding: str | None = None) -> bytes:
    """
    Coerce str/bytes into a strictly byte-wise HTTP header value.
    """
    ...

def _parse_content_type_charset(content_type: str) -> str | None:
    ...

def _parse_header_links(value: str) -> list[dict[str, str]]:
    """
    Returns a list of parsed link headers, for more info see:
    https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Link
    The generic syntax of those is:
    Link: < uri-reference >; param1=value1; param2="value2"
    So for instance:
    Link; '<http:/.../front.jpeg>; type="image/jpeg",<http://.../back.jpeg>;'
    would return
        [
            {"url": "http:/.../front.jpeg", "type": "image/jpeg"},
            {"url": "http://.../back.jpeg"},
        ]
    :param value: HTTP Link entity-header field
    :return: list of parsed link headers
    """
    ...

def _obfuscate_sensitive_headers(
    items: typing.Iterable[tuple[typing.AnyStr, typing.AnyStr]],
) -> typing.Iterator[tuple[typing.AnyStr, typing.AnyStr]]:
    ...

class Headers(typing.MutableMapping[str, str]):
    """
    HTTP headers, as a case-insensitive multi-dict.
    """
    def __init__(
        self,
        headers: HeaderTypes | None = None,
        encoding: str | None = None,
    ) -> None:
        ...

    @property
    def encoding(self) -> str:
        """
        Header encoding is mandated as ascii, but we allow fallbacks to utf-8
        or iso-8859-1.
        """
        ...

    @encoding.setter
    def encoding(self, value: str) -> None:
        ...

    @property
    def raw(self) -> list[tuple[bytes, bytes]]:
        """
        Returns a list of the raw header items, as byte pairs.
        """
        ...

    def keys(self) -> typing.KeysView[str]:
        ...

    def values(self) -> typing.ValuesView[str]:
        ...

    def items(self) -> typing.ItemsView[str, str]:
        """
        Return `(key, value)` items of headers. Concatenate headers
        into a single comma separated value when a key occurs multiple times.
        """
        ...

    def multi_items(self) -> list[tuple[str, str]]:
        """
        Return a list of `(key, value)` pairs of headers. Allow multiple
        occurrences of the same key without concatenating into a single
        comma separated value.
        """
        ...

    def get(self, key: str, default: typing.Any = None) -> typing.Any:
        """
        Return a header value. If multiple occurrences of the header occur
        then concatenate them together with commas.
        """
        ...

    def get_list(self, key: str, split_commas: bool = False) -> list[str]:
        """
        Return a list of all header values for a given key.
        If `split_commas=True` is passed, then any comma separated header
        values are split into multiple return strings.
        """
        ...

    def update(self, headers: HeaderTypes | None = None) -> None:  
        ...

    def copy(self) -> Headers:
        ...

    def __getitem__(self, key: str) -> str:
        """
        Return a single header value.
        If there are multiple headers with the same key, then we concatenate
        them with commas. See: https://tools.ietf.org/html/rfc7230
        """
        ...

    def __setitem__(self, key: str, value: str) -> None:
        """
        Set the header `key` to `value`, removing any duplicate entries.
        Retains insertion order.
        """
        ...

    def __delitem__(self, key: str) -> None:
        """
        Remove the header `key`.
        """
        ...

    def __contains__(self, key: typing.Any) -> bool:
        ...

    def __iter__(self) -> typing.Iterator[typing.Any]:
        ...

    def __len__(self) -> int:
        ...

    def __eq__(self, other: typing.Any) -> bool:
        ...

    def __repr__(self) -> str:
        ...

class Request:
    def __init__(
        self,
        method: str,
        url: URL | str,
        *,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        content: RequestContent | None = None,
        data: RequestData | None = None,
        files: RequestFiles | None = None,
        json: typing.Any | None = None,
        stream: SyncByteStream | AsyncByteStream | None = None,
        extensions: RequestExtensions | None = None,
    ) -> None:
        ...

    def _prepare(self, default_headers: dict[str, str]) -> None:
        ...

    @property
    def content(self) -> bytes:
        ...

    def read(self) -> bytes:
        """
        Read and return the request content.
        """
        ...

    async def aread(self) -> bytes:
        """
        Read and return the request content.
        """
        if not hasattr(self, "_content"):
            assert isinstance(self.stream, typing.AsyncIterable)
            self._content = b"".join([part async for part in self.stream])
            if not isinstance(self.stream, ByteStream):
                self.stream = ByteStream(self._content)
        return self._content
    def __repr__(self) -> str:
        ...

    def __getstate__(self) -> dict[str, typing.Any]:
        ...

    def __setstate__(self, state: dict[str, typing.Any]) -> None:
        ...

class Response:
    def __init__(
        self,
        status_code: int,
        *,
        headers: HeaderTypes | None = None,
        content: ResponseContent | None = None,
        text: str | None = None,
        html: str | None = None,
        json: typing.Any = None,
        stream: SyncByteStream | AsyncByteStream | None = None,
        request: Request | None = None,
        extensions: ResponseExtensions | None = None,
        history: list[Response] | None = None,
        default_encoding: str | typing.Callable[[bytes], str] = "utf-8",
    ) -> None:
        ...

    def _prepare(self, default_headers: dict[str, str]) -> None:
        ...

    @property
    def elapsed(self) -> datetime.timedelta:
        """
        Returns the time taken for the complete request/response
        cycle to complete.
        """
        ...

    @elapsed.setter
    def elapsed(self, elapsed: datetime.timedelta) -> None:
        ...

    @property
    def request(self) -> Request:
        """
        Returns the request instance associated to the current response.
        """
        ...

    @request.setter
    def request(self, value: Request) -> None:
        ...

    @property
    def http_version(self) -> str:
        ...

    @property
    def reason_phrase(self) -> str:
        ...

    @property
    def url(self) -> URL:
        """
        Returns the URL for which the request was made.
        """
        ...

    @property
    def content(self) -> bytes:
        ...

    @property
    def text(self) -> str:
        ...

    @property
    def encoding(self) -> str | None:
        """
        Return an encoding to use for decoding the byte content into text.
        The priority for determining this is given by...
        * `.encoding = <>` has been set explicitly.
        * The encoding as specified by the charset parameter in the Content-Type header.
        * The encoding as determined by `default_encoding`, which may either be
          a string like "utf-8" indicating the encoding to use, or may be a callable
          which enables charset autodetection.
        """
        ...

    @encoding.setter
    def encoding(self, value: str) -> None:
        """
        Set the encoding to use for decoding the byte content into text.
        If the `text` attribute has been accessed, attempting to set the
        encoding will throw a ValueError.
        """
        ...

    @property
    def charset_encoding(self) -> str | None:
        """
        Return the encoding, as specified by the Content-Type header.
        """
        ...

    def _get_content_decoder(self) -> ContentDecoder:
        """
        Returns a decoder instance which can be used to decode the raw byte
        content, depending on the Content-Encoding used in the response.
        """
        ...

    @property
    def is_informational(self) -> bool:
        """
        A property which is `True` for 1xx status codes, `False` otherwise.
        """
        ...

    @property
    def is_success(self) -> bool:
        """
        A property which is `True` for 2xx status codes, `False` otherwise.
        """
        ...

    @property
    def is_redirect(self) -> bool:
        """
        A property which is `True` for 3xx status codes, `False` otherwise.
        Note that not all responses with a 3xx status code indicate a URL redirect.
        Use `response.has_redirect_location` to determine responses with a properly
        formed URL redirection.
        """
        ...

    @property
    def is_client_error(self) -> bool:
        """
        A property which is `True` for 4xx status codes, `False` otherwise.
        """
        ...

    @property
    def is_server_error(self) -> bool:
        """
        A property which is `True` for 5xx status codes, `False` otherwise.
        """
        ...

    @property
    def is_error(self) -> bool:
        """
        A property which is `True` for 4xx and 5xx status codes, `False` otherwise.
        """
        ...

    @property
    def has_redirect_location(self) -> bool:
        """
        Returns True for 3xx responses with a properly formed URL redirection,
        `False` otherwise.
        """
        ...

    def raise_for_status(self) -> Response:
        """
        Raise the `HTTPStatusError` if one occurred.
        """
        ...

    def json(self, **kwargs: typing.Any) -> typing.Any:
        ...

    @property
    def cookies(self) -> Cookies:
        ...

    @property
    def links(self) -> dict[str | None, dict[str, str]]:
        """
        Returns the parsed header links of the response, if any
        """
        ...

    @property
    def num_bytes_downloaded(self) -> int:
        ...

    def __repr__(self) -> str:
        ...

    def __getstate__(self) -> dict[str, typing.Any]:
        ...

    def __setstate__(self, state: dict[str, typing.Any]) -> None:
        ...

    def read(self) -> bytes:
        """
        Read and return the response content.
        """
        ...

    def iter_bytes(self, chunk_size: int | None = None) -> typing.Iterator[bytes]:
        """
        A byte-iterator over the decoded response content.
        This allows us to handle gzip, deflate, brotli, and zstd encoded responses.
        """
        ...

    def iter_text(self, chunk_size: int | None = None) -> typing.Iterator[str]:
        """
        A str-iterator over the decoded response content
        that handles both gzip, deflate, etc but also detects the content's
        string encoding.
        """
        ...

    def iter_lines(self) -> typing.Iterator[str]:
        ...

    def iter_raw(self, chunk_size: int | None = None) -> typing.Iterator[bytes]:
        """
        A byte-iterator over the raw response content.
        """
        ...

    def close(self) -> None:
        """
        Close the response and release the connection.
        Automatically called if the response body is read to completion.
        """
        ...

    async def aread(self) -> bytes:
        """
        Read and return the response content.
        """
        if not hasattr(self, "_content"):
            self._content = b"".join([part async for part in self.aiter_bytes()])
        return self._content
    async def aiter_bytes(
        self, chunk_size: int | None = None
    ) -> typing.AsyncIterator[bytes]:
        """
        A byte-iterator over the decoded response content.
        This allows us to handle gzip, deflate, brotli, and zstd encoded responses.
        """
        if hasattr(self, "_content"):
            chunk_size = len(self._content) if chunk_size is None else chunk_size
            for i in range(0, len(self._content), max(chunk_size, 1)):
                yield self._content[i : i + chunk_size]
        else:
            decoder = self._get_content_decoder()
            chunker = ByteChunker(chunk_size=chunk_size)
            with request_context(request=self._request):
                async for raw_bytes in self.aiter_raw():
                    decoded = decoder.decode(raw_bytes)
                    for chunk in chunker.decode(decoded):
                        yield chunk
                decoded = decoder.flush()
                for chunk in chunker.decode(decoded):
                    yield chunk  
                for chunk in chunker.flush():
                    yield chunk
    async def aiter_text(
        self, chunk_size: int | None = None
    ) -> typing.AsyncIterator[str]:
        """
        A str-iterator over the decoded response content
        that handles both gzip, deflate, etc but also detects the content's
        string encoding.
        """
        decoder = TextDecoder(encoding=self.encoding or "utf-8")
        chunker = TextChunker(chunk_size=chunk_size)
        with request_context(request=self._request):
            async for byte_content in self.aiter_bytes():
                text_content = decoder.decode(byte_content)
                for chunk in chunker.decode(text_content):
                    yield chunk
            text_content = decoder.flush()
            for chunk in chunker.decode(text_content):
                yield chunk  
            for chunk in chunker.flush():
                yield chunk
    async def aiter_lines(self) -> typing.AsyncIterator[str]:
        decoder = LineDecoder()
        with request_context(request=self._request):
            async for text in self.aiter_text():
                for line in decoder.decode(text):
                    yield line
            for line in decoder.flush():
                yield line
    async def aiter_raw(
        self, chunk_size: int | None = None
    ) -> typing.AsyncIterator[bytes]:
        """
        A byte-iterator over the raw response content.
        """
        if self.is_stream_consumed:
            raise StreamConsumed()
        if self.is_closed:
            raise StreamClosed()
        if not isinstance(self.stream, AsyncByteStream):
            raise RuntimeError("Attempted to call an async iterator on a sync stream.")
        self.is_stream_consumed = True
        self._num_bytes_downloaded = 0
        chunker = ByteChunker(chunk_size=chunk_size)
        with request_context(request=self._request):
            async for raw_stream_bytes in self.stream:
                self._num_bytes_downloaded += len(raw_stream_bytes)
                for chunk in chunker.decode(raw_stream_bytes):
                    yield chunk
        for chunk in chunker.flush():
            yield chunk
        await self.aclose()
    async def aclose(self) -> None:
        """
        Close the response and release the connection.
        Automatically called if the response body is read to completion.
        """
        if not isinstance(self.stream, AsyncByteStream):
            raise RuntimeError("Attempted to call an async close on a sync stream.")
        if not self.is_closed:
            self.is_closed = True
            with request_context(request=self._request):
                await self.stream.aclose()
class Cookies(typing.MutableMapping[str, str]):
    """
    HTTP Cookies, as a mutable mapping.
    """
    def __init__(self, cookies: CookieTypes | None = None) -> None:
        ...

    def extract_cookies(self, response: Response) -> None:
        """
        Loads any cookies based on the response `Set-Cookie` headers.
        """
        ...

    def set_cookie_header(self, request: Request) -> None:
        """
        Sets an appropriate 'Cookie:' HTTP header on the `Request`.
        """
        ...

    def set(self, name: str, value: str, domain: str = "", path: str = "/") -> None:
        """
        Set a cookie value by name. May optionally include domain and path.
        """
        ...

    def get(  
        self,
        name: str,
        default: str | None = None,
        domain: str | None = None,
        path: str | None = None,
    ) -> str | None:
        """
        Get a cookie by name. May optionally include domain and path
        in order to specify exactly which cookie to retrieve.
        """
        ...

    def delete(
        self,
        name: str,
        domain: str | None = None,
        path: str | None = None,
    ) -> None:
        """
        Delete a cookie by name. May optionally include domain and path
        in order to specify exactly which cookie to delete.
        """
        ...

    def clear(self, domain: str | None = None, path: str | None = None) -> None:
        """
        Delete all cookies. Optionally include a domain and path in
        order to only delete a subset of all the cookies.
        """
        ...

    def update(self, cookies: CookieTypes | None = None) -> None:  
        ...

    def __setitem__(self, name: str, value: str) -> None:
        ...

    def __getitem__(self, name: str) -> str:
        ...

    def __delitem__(self, name: str) -> None:
        ...

    def __len__(self) -> int:
        ...

    def __iter__(self) -> typing.Iterator[str]:
        ...

    def __bool__(self) -> bool:
        ...

    def __repr__(self) -> str:
        ...

    class _CookieCompatRequest(urllib.request.Request):
        """
        Wraps a `Request` instance up in a compatibility interface suitable
        for use with `CookieJar` operations.
        """
        def __init__(self, request: Request) -> None:
            ...

        def add_unredirected_header(self, key: str, value: str) -> None:
            ...

    class _CookieCompatResponse:
        """
        Wraps a `Request` instance up in a compatibility interface suitable
        for use with `CookieJar` operations.
        """
        def __init__(self, response: Response) -> None:
            ...

        def info(self) -> email.message.Message:
            ...

