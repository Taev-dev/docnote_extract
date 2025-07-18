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
An implementation of `urlparse` that provides URL validation and normalization
as described by RFC3986.
We rely on this implementation rather than the one in Python's stdlib, because:
* It provides more complete URL validation.
* It properly differentiates between an empty querystring and an absent querystring,
  to distinguish URLs with a trailing '?'.
* It handles scheme, hostname, port, and path normalization.
* It supports IDNA hostnames, normalizing them to their encoded form.
* The API supports passing individual components, as well as the complete URL string.
Previously we relied on the excellent `rfc3986` package to handle URL parsing and
validation, but this module provides a simpler alternative, with less indirection
required.
"""
from __future__ import annotations
import ipaddress
import re
import typing
import idna
from ._exceptions import InvalidURL
MAX_URL_LENGTH = 65536
UNRESERVED_CHARACTERS = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)
SUB_DELIMS = "!$&'()*+,;="
PERCENT_ENCODED_REGEX = re.compile("%[A-Fa-f0-9]{2}")
FRAG_SAFE = "".join(
    [chr(i) for i in range(0x20, 0x7F) if i not in (0x20, 0x22, 0x3C, 0x3E, 0x60)]
)
QUERY_SAFE = "".join(
    [chr(i) for i in range(0x20, 0x7F) if i not in (0x20, 0x22, 0x23, 0x3C, 0x3E)]
)
PATH_SAFE = "".join(
    [
        chr(i)
        for i in range(0x20, 0x7F)
        if i not in (0x20, 0x22, 0x23, 0x3C, 0x3E) + (0x3F, 0x60, 0x7B, 0x7D)
    ]
)
USERNAME_SAFE = "".join(
    [
        chr(i)
        for i in range(0x20, 0x7F)
        if i
        not in (0x20, 0x22, 0x23, 0x3C, 0x3E)
        + (0x3F, 0x60, 0x7B, 0x7D)
        + (0x2F, 0x3A, 0x3B, 0x3D, 0x40, 0x5B, 0x5C, 0x5D, 0x5E, 0x7C)
    ]
)
PASSWORD_SAFE = "".join(
    [
        chr(i)
        for i in range(0x20, 0x7F)
        if i
        not in (0x20, 0x22, 0x23, 0x3C, 0x3E)
        + (0x3F, 0x60, 0x7B, 0x7D)
        + (0x2F, 0x3A, 0x3B, 0x3D, 0x40, 0x5B, 0x5C, 0x5D, 0x5E, 0x7C)
    ]
)
USERINFO_SAFE = "".join(
    [
        chr(i)
        for i in range(0x20, 0x7F)
        if i
        not in (0x20, 0x22, 0x23, 0x3C, 0x3E)
        + (0x3F, 0x60, 0x7B, 0x7D)
        + (0x2F, 0x3B, 0x3D, 0x40, 0x5B, 0x5C, 0x5D, 0x5E, 0x7C)
    ]
)
URL_REGEX = re.compile(
    (
        r"(?:(?P<scheme>{scheme}):)?"
        r"(?://(?P<authority>{authority}))?"
        r"(?P<path>{path})"
        r"(?:\?(?P<query>{query}))?"
        r"(?:
    ).format(
        scheme="([a-zA-Z][a-zA-Z0-9+.-]*)?",
        authority="[^/?
        path="[^?
        query="[^
        fragment=".*",
    )
)
AUTHORITY_REGEX = re.compile(
    (
        r"(?:(?P<userinfo>{userinfo})@)?" r"(?P<host>{host})" r":?(?P<port>{port})?"
    ).format(
        userinfo=".*",  
        host="(\\[.*\\]|[^:@]*)",  
        
        port=".*",  
    )
)
COMPONENT_REGEX = {
    "scheme": re.compile("([a-zA-Z][a-zA-Z0-9+.-]*)?"),
    "authority": re.compile("[^/?
    "path": re.compile("[^?
    "query": re.compile("[^
    "fragment": re.compile(".*"),
    "userinfo": re.compile("[^@]*"),
    "host": re.compile("(\\[.*\\]|[^:]*)"),
    "port": re.compile(".*"),
}
IPv4_STYLE_HOSTNAME = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$")
IPv6_STYLE_HOSTNAME = re.compile(r"^\[.*\]$")
class ParseResult(typing.NamedTuple):
    scheme: str
    userinfo: str
    host: str
    port: int | None
    path: str
    query: str | None
    fragment: str | None
    @property
    def authority(self) -> str:
        ...

    @property
    def netloc(self) -> str:
        ...

    def copy_with(self, **kwargs: str | None) -> ParseResult:
        ...

    def __str__(self) -> str:
        ...

def urlparse(url: str = "", **kwargs: str | None) -> ParseResult:
    ...

def encode_host(host: str) -> str:
    ...

def normalize_port(port: str | int | None, scheme: str) -> int | None:
    ...

def validate_path(path: str, has_scheme: bool, has_authority: bool) -> None:
    """
    Path validation rules that depend on if the URL contains
    a scheme or authority component.
    See https://datatracker.ietf.org/doc/html/rfc3986.html
    """
    ...

def normalize_path(path: str) -> str:
    """
    Drop "." and ".." segments from a URL path.
    For example:
        normalize_path("/path/./to/somewhere/..") == "/path/to"
    """
    ...

def PERCENT(string: str) -> str:
    ...

def percent_encoded(string: str, safe: str) -> str:
    """
    Use percent-encoding to quote a string.
    """
    ...

def quote(string: str, safe: str) -> str:
    """
    Use percent-encoding to quote a string, omitting existing '%xx' escape sequences.
    See: https://www.rfc-editor.org/rfc/rfc3986
    * `string`: The string to be percent-escaped.
    * `safe`: A string containing characters that may be treated as safe, and do not
        need to be escaped. Unreserved characters are always treated as safe.
        See: https://www.rfc-editor.org/rfc/rfc3986
    """
    ...

