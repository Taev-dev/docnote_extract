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
import typing
from .._models import Request, Response
from .._types import AsyncByteStream
from .base import AsyncBaseTransport
if typing.TYPE_CHECKING:  
    import asyncio
    import trio
    Event = typing.Union[asyncio.Event, trio.Event]
_Message = typing.MutableMapping[str, typing.Any]
_Receive = typing.Callable[[], typing.Awaitable[_Message]]
_Send = typing.Callable[
    [typing.MutableMapping[str, typing.Any]], typing.Awaitable[None]
]
_ASGIApp = typing.Callable[
    [typing.MutableMapping[str, typing.Any], _Receive, _Send], typing.Awaitable[None]
]
__all__ = ["ASGITransport"]
def is_running_trio() -> bool:
    ...

def create_event() -> Event:
    ...

class ASGIResponseStream(AsyncByteStream):
    def __init__(self, body: list[bytes]) -> None:
        ...

    async def __aiter__(self) -> typing.AsyncIterator[bytes]:
        yield b"".join(self._body)
class ASGITransport(AsyncBaseTransport):
    """
    A custom AsyncTransport that handles sending requests directly to an ASGI app.
    ```python
    transport = httpx.ASGITransport(
        app=app,
        root_path="/submount",
        client=("1.2.3.4", 123)
    )
    client = httpx.AsyncClient(transport=transport)
    ```
    Arguments:
    * `app` - The ASGI application.
    * `raise_app_exceptions` - Boolean indicating if exceptions in the application
       should be raised. Default to `True`. Can be set to `False` for use cases
       such as testing the content of a client 500 response.
    * `root_path` - The root path on which the ASGI application should be mounted.
    * `client` - A two-tuple indicating the client IP and port of incoming requests.
    ```
    """
    def __init__(
        self,
        app: _ASGIApp,
        raise_app_exceptions: bool = True,
        root_path: str = "",
        client: tuple[str, int] = ("127.0.0.1", 123),
    ) -> None:
        ...

    async def handle_async_request(
        self,
        request: Request,
    ) -> Response:
        assert isinstance(request.stream, AsyncByteStream)
        
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": request.method,
            "headers": [(k.lower(), v) for (k, v) in request.headers.raw],
            "scheme": request.url.scheme,
            "path": request.url.path,
            "raw_path": request.url.raw_path.split(b"?")[0],
            "query_string": request.url.query,
            "server": (request.url.host, request.url.port),
            "client": self.client,
            "root_path": self.root_path,
        }
        
        request_body_chunks = request.stream.__aiter__()
        request_complete = False
        
        status_code = None
        response_headers = None
        body_parts = []
        response_started = False
        response_complete = create_event()
        
        async def receive() -> dict[str, typing.Any]:
            nonlocal request_complete
            if request_complete:
                await response_complete.wait()
                return {"type": "http.disconnect"}
            try:
                body = await request_body_chunks.__anext__()
            except StopAsyncIteration:
                request_complete = True
                return {"type": "http.request", "body": b"", "more_body": False}
            return {"type": "http.request", "body": body, "more_body": True}
        async def send(message: typing.MutableMapping[str, typing.Any]) -> None:
            nonlocal status_code, response_headers, response_started
            if message["type"] == "http.response.start":
                assert not response_started
                status_code = message["status"]
                response_headers = message.get("headers", [])
                response_started = True
            elif message["type"] == "http.response.body":
                assert not response_complete.is_set()
                body = message.get("body", b"")
                more_body = message.get("more_body", False)
                if body and request.method != "HEAD":
                    body_parts.append(body)
                if not more_body:
                    response_complete.set()
        try:
            await self.app(scope, receive, send)
        except Exception:  
            if self.raise_app_exceptions:
                raise
            response_complete.set()
            if status_code is None:
                status_code = 500
            if response_headers is None:
                response_headers = {}
        assert response_complete.is_set()
        assert status_code is not None
        assert response_headers is not None
        stream = ASGIResponseStream(body_parts)
        return Response(status_code, headers=response_headers, stream=stream)
