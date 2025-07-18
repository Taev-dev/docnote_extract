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
import hashlib
import os
import re
import time
import typing
from base64 import b64encode
from urllib.request import parse_http_list
from ._exceptions import ProtocolError
from ._models import Cookies, Request, Response
from ._utils import to_bytes, to_str, unquote
if typing.TYPE_CHECKING:  
    from hashlib import _Hash
__all__ = ["Auth", "BasicAuth", "DigestAuth", "NetRCAuth"]
class Auth:
    """
    Base class for all authentication schemes.
    To implement a custom authentication scheme, subclass `Auth` and override
    the `.auth_flow()` method.
    If the authentication scheme does I/O such as disk access or network calls, or uses
    synchronization primitives such as locks, you should override `.sync_auth_flow()`
    and/or `.async_auth_flow()` instead of `.auth_flow()` to provide specialized
    implementations that will be used by `Client` and `AsyncClient` respectively.
    """
    requires_request_body = False
    requires_response_body = False
    def auth_flow(self, request: Request) -> typing.Generator[Request, Response, None]:
        """
        Execute the authentication flow.
        To dispatch a request, `yield` it:
        ```
        yield request
        ```
        The client will `.send()` the response back into the flow generator. You can
        access it like so:
        ```
        response = yield request
        ```
        A `return` (or reaching the end of the generator) will result in the
        client returning the last response obtained from the server.
        You can dispatch as many requests as is necessary.
        """
        ...

    def sync_auth_flow(
        self, request: Request
    ) -> typing.Generator[Request, Response, None]:
        """
        Execute the authentication flow synchronously.
        By default, this defers to `.auth_flow()`. You should override this method
        when the authentication scheme does I/O and/or uses concurrency primitives.
        """
        ...

    async def async_auth_flow(
        self, request: Request
    ) -> typing.AsyncGenerator[Request, Response]:
        """
        Execute the authentication flow asynchronously.
        By default, this defers to `.auth_flow()`. You should override this method
        when the authentication scheme does I/O and/or uses concurrency primitives.
        """
        if self.requires_request_body:
            await request.aread()
        flow = self.auth_flow(request)
        request = next(flow)
        while True:
            response = yield request
            if self.requires_response_body:
                await response.aread()
            try:
                request = flow.send(response)
            except StopIteration:
                break
class FunctionAuth(Auth):
    """
    Allows the 'auth' argument to be passed as a simple callable function,
    that takes the request, and returns a new, modified request.
    """
    def __init__(self, func: typing.Callable[[Request], Request]) -> None:
        ...

    def auth_flow(self, request: Request) -> typing.Generator[Request, Response, None]:
        ...

class BasicAuth(Auth):
    """
    Allows the 'auth' argument to be passed as a (username, password) pair,
    and uses HTTP Basic authentication.
    """
    def __init__(self, username: str | bytes, password: str | bytes) -> None:
        ...

    def auth_flow(self, request: Request) -> typing.Generator[Request, Response, None]:
        ...

    def _build_auth_header(self, username: str | bytes, password: str | bytes) -> str:
        ...

class NetRCAuth(Auth):
    """
    Use a 'netrc' file to lookup basic auth credentials based on the url host.
    """
    def __init__(self, file: str | None = None) -> None:
        ...

    def auth_flow(self, request: Request) -> typing.Generator[Request, Response, None]:
        ...

    def _build_auth_header(self, username: str | bytes, password: str | bytes) -> str:
        ...

class DigestAuth(Auth):
    _ALGORITHM_TO_HASH_FUNCTION: dict[str, typing.Callable[[bytes], _Hash]] = {
        "MD5": hashlib.md5,
        "MD5-SESS": hashlib.md5,
        "SHA": hashlib.sha1,
        "SHA-SESS": hashlib.sha1,
        "SHA-256": hashlib.sha256,
        "SHA-256-SESS": hashlib.sha256,
        "SHA-512": hashlib.sha512,
        "SHA-512-SESS": hashlib.sha512,
    }
    def __init__(self, username: str | bytes, password: str | bytes) -> None:
        ...

    def auth_flow(self, request: Request) -> typing.Generator[Request, Response, None]:
        ...

    def _parse_challenge(
        self, request: Request, response: Response, auth_header: str
    ) -> _DigestAuthChallenge:
        """
        Returns a challenge from a Digest WWW-Authenticate header.
        These take the form of:
        `Digest realm="realm@host.com",qop="auth,auth-int",nonce="abc",opaque="xyz"`
        """
        ...

    def _build_auth_header(
        self, request: Request, challenge: _DigestAuthChallenge
    ) -> str:
        ...

    def _get_client_nonce(self, nonce_count: int, nonce: bytes) -> bytes:
        ...

    def _get_header_value(self, header_fields: dict[str, bytes]) -> str:
        ...

    def _resolve_qop(self, qop: bytes | None, request: Request) -> bytes | None:
        ...

class _DigestAuthChallenge(typing.NamedTuple):
    realm: bytes
    nonce: bytes
    algorithm: str
    opaque: bytes | None
    qop: bytes | None
