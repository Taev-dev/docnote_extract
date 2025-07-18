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
import types
from abc import ABCMeta, abstractmethod
from collections.abc import AsyncGenerator, Callable, Coroutine, Iterable
from typing import Any, TypeVar
_T = TypeVar("_T")
class TestRunner(metaclass=ABCMeta):
    """
    Encapsulates a running event loop. Every call made through this object will use the
    same event loop.
    """
    def __enter__(self) -> TestRunner:
        ...

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> bool | None: ...
    @abstractmethod
    def run_asyncgen_fixture(
        self,
        fixture_func: Callable[..., AsyncGenerator[_T, Any]],
        kwargs: dict[str, Any],
    ) -> Iterable[_T]:
        """
        Run an async generator fixture.
        :param fixture_func: the fixture function
        :param kwargs: keyword arguments to call the fixture function with
        :return: an iterator yielding the value yielded from the async generator
        """
        """
        Run an async fixture.
        :param fixture_func: the fixture function
        :param kwargs: keyword arguments to call the fixture function with
        :return: the return value of the fixture function
        """
        """
        Run an async test function.
        :param test_func: the test function
        :param kwargs: keyword arguments to call the test function with
        """
    ...

