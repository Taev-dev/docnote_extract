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
Handlers for Content-Encoding.
See: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Encoding
"""
from __future__ import annotations
import codecs
import io
import typing
import zlib
from ._exceptions import DecodingError
try:
    import brotli
except ImportError:  
    try:
        import brotlicffi as brotli
    except ImportError:
        brotli = None
try:
    import zstandard
except ImportError:  
    zstandard = None  
class ContentDecoder:
    def decode(self, data: bytes) -> bytes:
        ...

    def flush(self) -> bytes:
        ...

class IdentityDecoder(ContentDecoder):
    """
    Handle unencoded data.
    """
    def decode(self, data: bytes) -> bytes:
        ...

    def flush(self) -> bytes:
        ...

class DeflateDecoder(ContentDecoder):
    """
    Handle 'deflate' decoding.
    See: https://stackoverflow.com/questions/1838699
    """
    def __init__(self) -> None:
        ...

    def decode(self, data: bytes) -> bytes:
        ...

    def flush(self) -> bytes:
        ...

class GZipDecoder(ContentDecoder):
    """
    Handle 'gzip' decoding.
    See: https://stackoverflow.com/questions/1838699
    """
    def __init__(self) -> None:
        ...

    def decode(self, data: bytes) -> bytes:
        ...

    def flush(self) -> bytes:
        ...

class BrotliDecoder(ContentDecoder):
    """
    Handle 'brotli' decoding.
    Requires `pip install brotlipy`. See: https://brotlipy.readthedocs.io/
        or   `pip install brotli`. See https://github.com/google/brotli
    Supports both 'brotlipy' and 'Brotli' packages since they share an import
    name. The top branches are for 'brotlipy' and bottom branches for 'Brotli'
    """
    def __init__(self) -> None:
        ...

    def decode(self, data: bytes) -> bytes:
        ...

    def flush(self) -> bytes:
        ...

class ZStandardDecoder(ContentDecoder):
    """
    Handle 'zstd' RFC 8878 decoding.
    Requires `pip install zstandard`.
    Can be installed as a dependency of httpx using `pip install httpx[zstd]`.
    """
    def __init__(self) -> None:
        ...

    def decode(self, data: bytes) -> bytes:
        ...

    def flush(self) -> bytes:
        ...

class MultiDecoder(ContentDecoder):
    """
    Handle the case where multiple encodings have been applied.
    """
    def __init__(self, children: typing.Sequence[ContentDecoder]) -> None:
        """
        'children' should be a sequence of decoders in the order in which
        each was applied.
        """
        ...

    def decode(self, data: bytes) -> bytes:
        ...

    def flush(self) -> bytes:
        ...

class ByteChunker:
    """
    Handles returning byte content in fixed-size chunks.
    """
    def __init__(self, chunk_size: int | None = None) -> None:
        ...

    def decode(self, content: bytes) -> list[bytes]:
        ...

    def flush(self) -> list[bytes]:
        ...

class TextChunker:
    """
    Handles returning text content in fixed-size chunks.
    """
    def __init__(self, chunk_size: int | None = None) -> None:
        ...

    def decode(self, content: str) -> list[str]:
        ...

    def flush(self) -> list[str]:
        ...

class TextDecoder:
    """
    Handles incrementally decoding bytes into text
    """
    def __init__(self, encoding: str = "utf-8") -> None:
        ...

    def decode(self, data: bytes) -> str:
        ...

    def flush(self) -> str:
        ...

class LineDecoder:
    """
    Handles incrementally reading lines from text.
    Has the same behaviour as the stdllib splitlines,
    but handling the input iteratively.
    """
    def __init__(self) -> None:
        ...

    def decode(self, text: str) -> list[str]:
        ...

    def flush(self) -> list[str]:
        ...

SUPPORTED_DECODERS = {
    "identity": IdentityDecoder,
    "gzip": GZipDecoder,
    "deflate": DeflateDecoder,
    "br": BrotliDecoder,
    "zstd": ZStandardDecoder,
}
if brotli is None:
    SUPPORTED_DECODERS.pop("br")  
if zstandard is None:
    SUPPORTED_DECODERS.pop("zstd")  
