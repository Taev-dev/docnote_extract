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

"""
Type definitions for type checking purposes.
"""
from http.cookiejar import CookieJar
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    AsyncIterable,
    AsyncIterator,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)
if TYPE_CHECKING:  
    from ._auth import Auth  
    from ._config import Proxy, Timeout  
    from ._models import Cookies, Headers, Request  
    from ._urls import URL, QueryParams  
PrimitiveData = Optional[Union[str, int, float, bool]]
URLTypes = Union["URL", str]
QueryParamTypes = Union[
    "QueryParams",
    Mapping[str, Union[PrimitiveData, Sequence[PrimitiveData]]],
    List[Tuple[str, PrimitiveData]],
    Tuple[Tuple[str, PrimitiveData], ...],
    str,
    bytes,
]
HeaderTypes = Union[
    "Headers",
    Mapping[str, str],
    Mapping[bytes, bytes],
    Sequence[Tuple[str, str]],
    Sequence[Tuple[bytes, bytes]],
]
CookieTypes = Union["Cookies", CookieJar, Dict[str, str], List[Tuple[str, str]]]
TimeoutTypes = Union[
    Optional[float],
    Tuple[Optional[float], Optional[float], Optional[float], Optional[float]],
    "Timeout",
]
ProxyTypes = Union["URL", str, "Proxy"]
CertTypes = Union[str, Tuple[str, str], Tuple[str, str, str]]
AuthTypes = Union[
    Tuple[Union[str, bytes], Union[str, bytes]],
    Callable[["Request"], "Request"],
    "Auth",
]
RequestContent = Union[str, bytes, Iterable[bytes], AsyncIterable[bytes]]
ResponseContent = Union[str, bytes, Iterable[bytes], AsyncIterable[bytes]]
ResponseExtensions = Mapping[str, Any]
RequestData = Mapping[str, Any]
FileContent = Union[IO[bytes], bytes, str]
FileTypes = Union[
    FileContent,
    Tuple[Optional[str], FileContent],
    Tuple[Optional[str], FileContent, Optional[str]],
    Tuple[Optional[str], FileContent, Optional[str], Mapping[str, str]],
]
RequestFiles = Union[Mapping[str, FileTypes], Sequence[Tuple[str, FileTypes]]]
RequestExtensions = Mapping[str, Any]
__all__ = ["AsyncByteStream", "SyncByteStream"]
class SyncByteStream:
    def __iter__(self) -> Iterator[bytes]:
        ...

    def close(self) -> None:
        """
        Subclasses can override this method to release any network resources
        after a request/response cycle is complete.
        """
