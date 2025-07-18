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
import io
import itertools
import sys
import typing
from .._models import Request, Response
from .._types import SyncByteStream
from .base import BaseTransport
if typing.TYPE_CHECKING:
    from _typeshed import OptExcInfo  
    from _typeshed.wsgi import WSGIApplication  
_T = typing.TypeVar("_T")
__all__ = ["WSGITransport"]
def _skip_leading_empty_chunks(body: typing.Iterable[_T]) -> typing.Iterable[_T]:
    ...

class WSGIByteStream(SyncByteStream):
    def __init__(self, result: typing.Iterable[bytes]) -> None:
        ...

    def __iter__(self) -> typing.Iterator[bytes]:
        ...

    def close(self) -> None:
        ...

class WSGITransport(BaseTransport):
    """
    A custom transport that handles sending requests directly to an WSGI app.
    The simplest way to use this functionality is to use the `app` argument.
    ```
    client = httpx.Client(app=app)
    ```
    Alternatively, you can setup the transport instance explicitly.
    This allows you to include any additional configuration arguments specific
    to the WSGITransport class:
    ```
    transport = httpx.WSGITransport(
        app=app,
        script_name="/submount",
        remote_addr="1.2.3.4"
    )
    client = httpx.Client(transport=transport)
    ```
    Arguments:
    * `app` - The WSGI application.
    * `raise_app_exceptions` - Boolean indicating if exceptions in the application
       should be raised. Default to `True`. Can be set to `False` for use cases
       such as testing the content of a client 500 response.
    * `script_name` - The root path on which the WSGI application should be mounted.
    * `remote_addr` - A string indicating the client IP of incoming requests.
    ```
    """
    def __init__(
        self,
        app: WSGIApplication,
        raise_app_exceptions: bool = True,
        script_name: str = "",
        remote_addr: str = "127.0.0.1",
        wsgi_errors: typing.TextIO | None = None,
    ) -> None:
        ...

    def handle_request(self, request: Request) -> Response:
        ...

