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
import io
import mimetypes
import os
import re
import typing
from pathlib import Path
from ._types import (
    AsyncByteStream,
    FileContent,
    FileTypes,
    RequestData,
    RequestFiles,
    SyncByteStream,
)
from ._utils import (
    peek_filelike_length,
    primitive_value_to_str,
    to_bytes,
)
_HTML5_FORM_ENCODING_REPLACEMENTS = {'"': "%22", "\\": "\\\\"}
_HTML5_FORM_ENCODING_REPLACEMENTS.update(
    {chr(c): "%{:02X}".format(c) for c in range(0x1F + 1) if c != 0x1B}
)
_HTML5_FORM_ENCODING_RE = re.compile(
    r"|".join([re.escape(c) for c in _HTML5_FORM_ENCODING_REPLACEMENTS.keys()])
)
def _format_form_param(name: str, value: str) -> bytes:
    """
    Encode a name/value pair within a multipart form.
    """
    ...

def _guess_content_type(filename: str | None) -> str | None:
    """
    Guesses the mimetype based on a filename. Defaults to `application/octet-stream`.
    Returns `None` if `filename` is `None` or empty.
    """
    ...

def get_multipart_boundary_from_content_type(
    content_type: bytes | None,
) -> bytes | None:
    ...

class DataField:
    """
    A single form field item, within a multipart form field.
    """
    def __init__(self, name: str, value: str | bytes | int | float | None) -> None:
        ...

    def render_headers(self) -> bytes:
        ...

    def render_data(self) -> bytes:
        ...

    def get_length(self) -> int:
        ...

    def render(self) -> typing.Iterator[bytes]:
        ...

class FileField:
    """
    A single file field item, within a multipart form field.
    """
    CHUNK_SIZE = 64 * 1024
    def __init__(self, name: str, value: FileTypes) -> None:
        ...

    def get_length(self) -> int | None:
        ...

    def render_headers(self) -> bytes:
        ...

    def render_data(self) -> typing.Iterator[bytes]:
        ...

    def render(self) -> typing.Iterator[bytes]:
        ...

class MultipartStream(SyncByteStream, AsyncByteStream):
    """
    Request content as streaming multipart encoded form data.
    """
    def __init__(
        self,
        data: RequestData,
        files: RequestFiles,
        boundary: bytes | None = None,
    ) -> None:
        ...

    def _iter_fields(
        self, data: RequestData, files: RequestFiles
    ) -> typing.Iterator[FileField | DataField]:
        ...

    def iter_chunks(self) -> typing.Iterator[bytes]:
        ...

    def get_content_length(self) -> int | None:
        """
        Return the length of the multipart encoded content, or `None` if
        any of the files have a length that cannot be determined upfront.
        """
        ...

    def get_headers(self) -> dict[str, str]:
        ...

    def __iter__(self) -> typing.Iterator[bytes]:
        ...

    async def __aiter__(self) -> typing.AsyncIterator[bytes]:
        for chunk in self.iter_chunks():
            yield chunk
