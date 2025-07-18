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
import ipaddress
import os
import re
import typing
from urllib.request import getproxies
from ._types import PrimitiveData
if typing.TYPE_CHECKING:  
    from ._urls import URL
def primitive_value_to_str(value: PrimitiveData) -> str:
    """
    Coerce a primitive data type into a string value.
    Note that we prefer JSON-style 'true'/'false' for boolean values here.
    """
    ...

def get_environment_proxies() -> dict[str, str | None]:
    """Gets proxy information from the environment"""
    proxy_info = getproxies()
    mounts: dict[str, str | None] = {}
    for scheme in ("http", "https", "all"):
        if proxy_info.get(scheme):
            hostname = proxy_info[scheme]
            mounts[f"{scheme}://"] = (
                hostname if "://" in hostname else f"http://{hostname}"
            )
    no_proxy_hosts = [host.strip() for host in proxy_info.get("no", "").split(",")]
    for hostname in no_proxy_hosts:
        if hostname == "*":
            return {}
        elif hostname:
            if "://" in hostname:
                mounts[hostname] = None
            elif is_ipv4_hostname(hostname):
                mounts[f"all://{hostname}"] = None
            elif is_ipv6_hostname(hostname):
                mounts[f"all://[{hostname}]"] = None
            elif hostname.lower() == "localhost":
                mounts[f"all://{hostname}"] = None
            else:
                mounts[f"all://*{hostname}"] = None
    return mounts
def to_bytes(value: str | bytes, encoding: str = "utf-8") -> bytes:
    return value.encode(encoding) if isinstance(value, str) else value
def to_str(value: str | bytes, encoding: str = "utf-8") -> str:
    return value if isinstance(value, str) else value.decode(encoding)
def to_bytes_or_str(value: str, match_type_of: typing.AnyStr) -> typing.AnyStr:
    return value if isinstance(match_type_of, str) else value.encode()
def unquote(value: str) -> str:
    return value[1:-1] if value[0] == value[-1] == '"' else value
def peek_filelike_length(stream: typing.Any) -> int | None:
    """
    ...

class URLPattern:
    """
    A utility class currently used for making lookups against proxy keys...
    
    >>> pattern = URLPattern("all://")
    >>> pattern.matches(httpx.URL("http://example.com"))
    True
    
    >>> pattern = URLPattern("https://")
    >>> pattern.matches(httpx.URL("https://example.com"))
    True
    >>> pattern.matches(httpx.URL("http://example.com"))
    False
    
    >>> pattern = URLPattern("https://example.com")
    >>> pattern.matches(httpx.URL("https://example.com"))
    True
    >>> pattern.matches(httpx.URL("http://example.com"))
    False
    >>> pattern.matches(httpx.URL("https://other.com"))
    False
    
    >>> pattern = URLPattern("all://example.com")
    >>> pattern.matches(httpx.URL("https://example.com"))
    True
    >>> pattern.matches(httpx.URL("http://example.com"))
    True
    >>> pattern.matches(httpx.URL("https://other.com"))
    False
    
    >>> pattern = URLPattern("https://example.com:1234")
    >>> pattern.matches(httpx.URL("https://example.com:1234"))
    True
    >>> pattern.matches(httpx.URL("https://example.com"))
    False
    """
    def __init__(self, pattern: str) -> None:
        ...

    def matches(self, other: URL) -> bool:
        ...

    @property
    def priority(self) -> tuple[int, int, int]:
        """
        The priority allows URLPattern instances to be sortable, so that
        we can match from most specific to least specific.
        """
        ...

    def __hash__(self) -> int:
        ...

    def __lt__(self, other: URLPattern) -> bool:
        ...

    def __eq__(self, other: typing.Any) -> bool:
        ...

def is_ipv4_hostname(hostname: str) -> bool:
    ...

def is_ipv6_hostname(hostname: str) -> bool:
    ...

