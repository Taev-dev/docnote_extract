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
import functools
import json
import sys
import typing
import click
import pygments.lexers
import pygments.util
import rich.console
import rich.markup
import rich.progress
import rich.syntax
import rich.table
from ._client import Client
from ._exceptions import RequestError
from ._models import Response
from ._status_codes import codes
if typing.TYPE_CHECKING:
    import httpcore  
def print_help() -> None:
    ...

def get_lexer_for_response(response: Response) -> str:
    ...

def format_request_headers(request: httpcore.Request, http2: bool = False) -> str:
    ...

def format_response_headers(
    http_version: bytes,
    status: int,
    reason_phrase: bytes | None,
    headers: list[tuple[bytes, bytes]],
) -> str:
    ...

def print_request_headers(request: httpcore.Request, http2: bool = False) -> None:
    ...

def print_response_headers(
    http_version: bytes,
    status: int,
    reason_phrase: bytes | None,
    headers: list[tuple[bytes, bytes]],
) -> None:
    ...

def print_response(response: Response) -> None:
    ...

_PCTRTT = typing.Tuple[typing.Tuple[str, str], ...]
_PCTRTTT = typing.Tuple[_PCTRTT, ...]
_PeerCertRetDictType = typing.Dict[str, typing.Union[str, _PCTRTTT, _PCTRTT]]
def format_certificate(cert: _PeerCertRetDictType) -> str:  
    ...

def trace(
    name: str, info: typing.Mapping[str, typing.Any], verbose: bool = False
) -> None:
    ...

def download_response(response: Response, download: typing.BinaryIO) -> None:
    ...

def validate_json(
    ctx: click.Context,
    param: click.Option | click.Parameter,
    value: typing.Any,
) -> typing.Any:
    ...

def validate_auth(
    ctx: click.Context,
    param: click.Option | click.Parameter,
    value: typing.Any,
) -> typing.Any:
    ...

def handle_help(
    ctx: click.Context,
    param: click.Option | click.Parameter,
    value: typing.Any,
) -> None:
    ...

@click.command(add_help_option=False)
@click.argument("url", type=str)
@click.option(
    "--method",
    "-m",
    "method",
    type=str,
    help=(
        "Request method, such as GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD. "
        "[Default: GET, or POST if a request body is included]"
    ),
)
@click.option(
    "--params",
    "-p",
    "params",
    type=(str, str),
    multiple=True,
    help="Query parameters to include in the request URL.",
)
@click.option(
    "--content",
    "-c",
    "content",
    type=str,
    help="Byte content to include in the request body.",
)
@click.option(
    "--data",
    "-d",
    "data",
    type=(str, str),
    multiple=True,
    help="Form data to include in the request body.",
)
@click.option(
    "--files",
    "-f",
    "files",
    type=(str, click.File(mode="rb")),
    multiple=True,
    help="Form files to include in the request body.",
)
@click.option(
    "--json",
    "-j",
    "json",
    type=str,
    callback=validate_json,
    help="JSON data to include in the request body.",
)
@click.option(
    "--headers",
    "-h",
    "headers",
    type=(str, str),
    multiple=True,
    help="Include additional HTTP headers in the request.",
)
@click.option(
    "--cookies",
    "cookies",
    type=(str, str),
    multiple=True,
    help="Cookies to include in the request.",
)
@click.option(
    "--auth",
    "auth",
    type=(str, str),
    default=(None, None),
    ...

)
@click.option(
    "--proxy",
    "proxy",
    type=str,
    default=None,
    help="Send the request via a proxy. Should be the URL giving the proxy address.",
)
@click.option(
    ...

)
@click.option(
    "--follow-redirects",
    "follow_redirects",
    is_flag=True,
    default=False,
    help="Automatically follow redirects.",
)
@click.option(
    ...

)
@click.option(
    "--http2",
    "http2",
    type=bool,
    is_flag=True,
    default=False,
    help="Send the request using HTTP/2, if the remote server supports it.",
)
@click.option(
    ...

)
@click.option(
    "--verbose",
    "-v",
    type=bool,
    is_flag=True,
    default=False,
    help="Verbose. Show request as well as response.",
)
@click.option(
    ...

)
def main(
    url: str,
    method: str,
    params: list[tuple[str, str]],
    content: str,
    data: list[tuple[str, str]],
    files: list[tuple[str, click.File]],
    json: str,
    headers: list[tuple[str, str]],
    cookies: list[tuple[str, str]],
    auth: tuple[str, str] | None,
    proxy: str,
    timeout: float,
    follow_redirects: bool,
    verify: bool,
    http2: bool,
    download: typing.BinaryIO | None,
    verbose: bool,
) -> None:
    """
    An HTTP command line client.
    Sends a request and displays the response.
    """
    ...

