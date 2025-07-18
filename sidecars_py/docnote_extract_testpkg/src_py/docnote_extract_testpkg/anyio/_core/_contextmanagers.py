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
from abc import abstractmethod
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from inspect import isasyncgen, iscoroutine, isgenerator
from types import TracebackType
from typing import Protocol, TypeVar, cast, final
_T_co = TypeVar("_T_co", covariant=True)
_ExitT_co = TypeVar("_ExitT_co", covariant=True, bound="bool | None")
class _SupportsCtxMgr(Protocol[_T_co, _ExitT_co]):
    def __contextmanager__(self) -> AbstractContextManager[_T_co, _ExitT_co]: ...
class _SupportsAsyncCtxMgr(Protocol[_T_co, _ExitT_co]):
    def __asynccontextmanager__(
        self,
    ) -> AbstractAsyncContextManager[_T_co, _ExitT_co]: ...
class ContextManagerMixin:
    """
    Mixin class providing context manager functionality via a generator-based
    implementation.
    This class allows you to implement a context manager via :meth:`__contextmanager__`
    which should return a generator. The mechanics are meant to mirror those of
    :func:`@contextmanager <contextlib.contextmanager>`.
    .. note:: Classes using this mix-in are not reentrant as context managers, meaning
        that once you enter it, you can't re-enter before first exiting it.
    .. seealso:: :doc:`contextmanagers`
    """
    __cm: AbstractContextManager[object, bool | None] | None = None
    @final
    def __enter__(self: _SupportsCtxMgr[_T_co, bool | None]) -> _T_co:
        ...

    @final
    def __exit__(
        self: _SupportsCtxMgr[object, _ExitT_co],
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> _ExitT_co:
        ...

    @abstractmethod
    def __contextmanager__(self) -> AbstractContextManager[object, bool | None]:
        """
        Implement your context manager logic here.
        This method **must** be decorated with
        :func:`@contextmanager <contextlib.contextmanager>`.
        .. note:: Remember that the ``yield`` will raise any exception raised in the
            enclosed context block, so use a ``finally:`` block to clean up resources!
        :return: a context manager object
        """
    """
    Mixin class providing async context manager functionality via a generator-based
    implementation.
    This class allows you to implement a context manager via
    :meth:`__asynccontextmanager__`. The mechanics are meant to mirror those of
    :func:`@asynccontextmanager <contextlib.asynccontextmanager>`.
    .. note:: Classes using this mix-in are not reentrant as context managers, meaning
        that once you enter it, you can't re-enter before first exiting it.
    .. seealso:: :doc:`contextmanagers`
    """
        """
        Implement your async context manager logic here.
        This method **must** be decorated with
        :func:`@asynccontextmanager <contextlib.asynccontextmanager>`.
        .. note:: Remember that the ``yield`` will raise any exception raised in the
            enclosed context block, so use a ``finally:`` block to clean up resources!
        :return: an async context manager object
        """
