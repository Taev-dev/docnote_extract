"""This is a programmatically-vendored code sample
that has been stubbified (ie, function bodies removed). Do not modify
it directly; your changes will just be overwritten.

The original source is:
PkgSrcSpec(forge='github',
           repo_id='agronholm/anyio',
           pkg_name='anyio',
           offset_dest_root_dir=None,
           root_path='src/anyio',
           commit_hash='65fe287039e2ded48752e1111a82c29d07725e36',
           license_paths={'LICENSE'})

The license of the original project is included in the top level of
the vendored project directory.

To regenerate, see sidecars/docnote_extract_testpkg_factory. The
command is:
``uv run python -m docnote_extract_testpkg_factory``.

"""
from __future__ import annotations
from abc import ABCMeta, abstractmethod
from types import TracebackType
from typing import TypeVar
T = TypeVar("T")
class AsyncResource(metaclass=ABCMeta):
    """
    Abstract base class for all closeable asynchronous resources.
    Works as an asynchronous context manager which returns the instance itself on enter,
    and calls :meth:`aclose` on exit.
    """
    __slots__ = ()
    async def __aenter__(self: T) -> T:
        return self
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()
    @abstractmethod
    async def aclose(self) -> None:
        """Close the resource."""
