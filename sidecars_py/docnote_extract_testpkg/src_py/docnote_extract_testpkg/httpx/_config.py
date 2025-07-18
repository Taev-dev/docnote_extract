# This is a programmatically-vendored code sample
# that has been stubbified (ie, function bodies removed). Do not modify
# it directly; your changes will just be overwritten.

# The original source is:
# PkgSrcSpec(forge='github',
#            repo_id='encode/httpx',
#            pkg_name='httpx',
#            offset_dest_root_dir=None,
#            root_path='httpx',
#            commit_hash='4fb9528c2f5ac000441c3634d297e77da23067cd',
#            license_paths={'LICENSE.md'})

# The license of the original project is included in the top level of
# the vendored project directory.

# To regenerate, see sidecars/docnote_extract_testpkg_factory. The
# command is:
# ``uv run python -m docnote_extract_testpkg_factory``.

from __future__ import annotations
import os
import typing
from ._models import Headers
from ._types import CertTypes, HeaderTypes, TimeoutTypes
from ._urls import URL
if typing.TYPE_CHECKING:
    import ssl  
__all__ = ["Limits", "Proxy", "Timeout", "create_ssl_context"]
class UnsetType:
    pass  
UNSET = UnsetType()
def create_ssl_context(
    verify: ssl.SSLContext | str | bool = True,
    cert: CertTypes | None = None,
    trust_env: bool = True,
) -> ssl.SSLContext:
    ...

class Timeout:
    """
    Timeout configuration.
    **Usage**:
    Timeout(None)               
    Timeout(5.0)                
    Timeout(None, connect=5.0)  
    Timeout(5.0, connect=10.0)  
    Timeout(5.0, pool=None)     
    """
    def __init__(
        self,
        timeout: TimeoutTypes | UnsetType = UNSET,
        *,
        connect: None | float | UnsetType = UNSET,
        read: None | float | UnsetType = UNSET,
        write: None | float | UnsetType = UNSET,
        pool: None | float | UnsetType = UNSET,
    ) -> None:
        ...

    def as_dict(self) -> dict[str, float | None]:
        ...

    def __eq__(self, other: typing.Any) -> bool:
        ...

    def __repr__(self) -> str:
        ...

class Limits:
    """
    Configuration for limits to various client behaviors.
    **Parameters:**
    * **max_connections** - The maximum number of concurrent connections that may be
            established.
    * **max_keepalive_connections** - Allow the connection pool to maintain
            keep-alive connections below this point. Should be less than or equal
            to `max_connections`.
    * **keepalive_expiry** - Time limit on idle keep-alive connections in seconds.
    """
    def __init__(
        self,
        *,
        max_connections: int | None = None,
        max_keepalive_connections: int | None = None,
        keepalive_expiry: float | None = 5.0,
    ) -> None:
        ...

    def __eq__(self, other: typing.Any) -> bool:
        ...

    def __repr__(self) -> str:
        ...

class Proxy:
    def __init__(
        self,
        url: URL | str,
        *,
        ssl_context: ssl.SSLContext | None = None,
        auth: tuple[str, str] | None = None,
        headers: HeaderTypes | None = None,
    ) -> None:
        ...

    @property
    def raw_auth(self) -> tuple[bytes, bytes] | None:
        ...

    def __repr__(self) -> str:
        ...

DEFAULT_TIMEOUT_CONFIG = Timeout(timeout=5.0)
DEFAULT_LIMITS = Limits(max_connections=100, max_keepalive_connections=20)
DEFAULT_MAX_REDIRECTS = 20
