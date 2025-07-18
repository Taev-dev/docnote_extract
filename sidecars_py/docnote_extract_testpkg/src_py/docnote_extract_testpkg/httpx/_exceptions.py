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
"""
Our exception hierarchy:
* HTTPError
  x RequestError
    + TransportError
      - TimeoutException
        · ConnectTimeout
        · ReadTimeout
        · WriteTimeout
        · PoolTimeout
      - NetworkError
        · ConnectError
        · ReadError
        · WriteError
        · CloseError
      - ProtocolError
        · LocalProtocolError
        · RemoteProtocolError
      - ProxyError
      - UnsupportedProtocol
    + DecodingError
    + TooManyRedirects
  x HTTPStatusError
* InvalidURL
* CookieConflict
* StreamError
  x StreamConsumed
  x StreamClosed
  x ResponseNotRead
  x RequestNotRead
"""
from __future__ import annotations
import contextlib
import typing
if typing.TYPE_CHECKING:
    from ._models import Request, Response  
__all__ = [
    "CloseError",
    "ConnectError",
    "ConnectTimeout",
    "CookieConflict",
    "DecodingError",
    "HTTPError",
    "HTTPStatusError",
    "InvalidURL",
    "LocalProtocolError",
    "NetworkError",
    "PoolTimeout",
    "ProtocolError",
    "ProxyError",
    "ReadError",
    "ReadTimeout",
    "RemoteProtocolError",
    "RequestError",
    "RequestNotRead",
    "ResponseNotRead",
    "StreamClosed",
    "StreamConsumed",
    "StreamError",
    "TimeoutException",
    "TooManyRedirects",
    "TransportError",
    "UnsupportedProtocol",
    "WriteError",
    "WriteTimeout",
]
class HTTPError(Exception):
    """
    Base class for `RequestError` and `HTTPStatusError`.
    Useful for `try...except` blocks when issuing a request,
    and then calling `.raise_for_status()`.
    For example:
    ```
    try:
        response = httpx.get("https://www.example.com")
        response.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"HTTP Exception for {exc.request.url} - {exc}")
    ```
    """
    def __init__(self, message: str) -> None:
        ...

    @property
    def request(self) -> Request:
        ...

    @request.setter
    def request(self, request: Request) -> None:
        ...

class RequestError(HTTPError):
    """
    Base class for all exceptions that may occur when issuing a `.request()`.
    """
    def __init__(self, message: str, *, request: Request | None = None) -> None:
        ...

class TransportError(RequestError):
    """
    Base class for all exceptions that occur at the level of the Transport API.
    """
class TimeoutException(TransportError):
    """
    The base class for timeout errors.
    An operation has timed out.
    """
class ConnectTimeout(TimeoutException):
    """
    Timed out while connecting to the host.
    """
class ReadTimeout(TimeoutException):
    """
    Timed out while receiving data from the host.
    """
class WriteTimeout(TimeoutException):
    """
    Timed out while sending data to the host.
    """
class PoolTimeout(TimeoutException):
    """
    Timed out waiting to acquire a connection from the pool.
    """
class NetworkError(TransportError):
    """
    The base class for network-related errors.
    An error occurred while interacting with the network.
    """
class ReadError(NetworkError):
    """
    Failed to receive data from the network.
    """
class WriteError(NetworkError):
    """
    Failed to send data through the network.
    """
class ConnectError(NetworkError):
    """
    Failed to establish a connection.
    """
class CloseError(NetworkError):
    """
    Failed to close a connection.
    """
class ProxyError(TransportError):
    """
    An error occurred while establishing a proxy connection.
    """
class UnsupportedProtocol(TransportError):
    """
    Attempted to make a request to an unsupported protocol.
    For example issuing a request to `ftp://www.example.com`.
    """
class ProtocolError(TransportError):
    """
    The protocol was violated.
    """
class LocalProtocolError(ProtocolError):
    """
    A protocol was violated by the client.
    For example if the user instantiated a `Request` instance explicitly,
    failed to include the mandatory `Host:` header, and then issued it directly
    using `client.send()`.
    """
class RemoteProtocolError(ProtocolError):
    """
    The protocol was violated by the server.
    For example, returning malformed HTTP.
    """
class DecodingError(RequestError):
    """
    Decoding of the response failed, due to a malformed encoding.
    """
class TooManyRedirects(RequestError):
    """
    Too many redirects.
    """
class HTTPStatusError(HTTPError):
    """
    The response had an error HTTP status of 4xx or 5xx.
    May be raised when calling `response.raise_for_status()`
    """
    def __init__(self, message: str, *, request: Request, response: Response) -> None:
        ...

class InvalidURL(Exception):
    """
    URL is improperly formed or cannot be parsed.
    """
    def __init__(self, message: str) -> None:
        ...

class CookieConflict(Exception):
    """
    Attempted to lookup a cookie by name, but multiple cookies existed.
    Can occur when calling `response.cookies.get(...)`.
    """
    def __init__(self, message: str) -> None:
        ...

class StreamError(RuntimeError):
    """
    The base class for stream exceptions.
    The developer made an error in accessing the request stream in
    an invalid way.
    """
    def __init__(self, message: str) -> None:
        ...

class StreamConsumed(StreamError):
    """
    Attempted to read or stream content, but the content has already
    been streamed.
    """
    def __init__(self) -> None:
        ...

class StreamClosed(StreamError):
    """
    Attempted to read or stream response content, but the request has been
    closed.
    """
    def __init__(self) -> None:
        ...

class ResponseNotRead(StreamError):
    """
    Attempted to access streaming response content, without having called `read()`.
    """
    def __init__(self) -> None:
        ...

class RequestNotRead(StreamError):
    """
    Attempted to access streaming request content, without having called `read()`.
    """
    def __init__(self) -> None:
        ...

@contextlib.contextmanager
def request_context(
    request: Request | None = None,
) -> typing.Iterator[None]:
    """
    A context manager that can be used to attach the given request context
    to any `RequestError` exceptions that are raised within the block.
    """
    ...

