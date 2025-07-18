# This is a programmatically-vendored code sample
# that has been stubbified (ie, function bodies removed). Do not modify
# it directly; your changes will just be overwritten.

# The original source is:
# PkgSrcSpec(forge='github',
#            repo_id='agronholm/anyio',
#            pkg_name='anyio',
#            offset_dest_root_dir=None,
#            root_path='src/anyio',
#            commit_hash='65fe287039e2ded48752e1111a82c29d07725e36',
#            license_paths={'LICENSE'})

# The license of the original project is included in the top level of
# the vendored project directory.

# To regenerate, see sidecars/docnote_extract_testpkg_factory. The
# command is:
# ``uv run python -m docnote_extract_testpkg_factory``.

from __future__ import annotations
import asyncio
import socket
import threading
from collections.abc import Callable
from selectors import EVENT_READ, EVENT_WRITE, DefaultSelector
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from _typeshed import FileDescriptorLike
_selector_lock = threading.Lock()
_selector: Selector | None = None
class Selector:
    def __init__(self) -> None:
        ...

    def start(self) -> None:
        ...

    def _stop(self) -> None:
        ...

    def _notify_self(self) -> None:
        ...

    def add_reader(self, fd: FileDescriptorLike, callback: Callable[[], Any]) -> None:
        ...

    def add_writer(self, fd: FileDescriptorLike, callback: Callable[[], Any]) -> None:
        ...

    def remove_reader(self, fd: FileDescriptorLike) -> bool:
        ...

    def remove_writer(self, fd: FileDescriptorLike) -> bool:
        ...

    def run(self) -> None:
        ...

def get_selector() -> Selector:
    ...

