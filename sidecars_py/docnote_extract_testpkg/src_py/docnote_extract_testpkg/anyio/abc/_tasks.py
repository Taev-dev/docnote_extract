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
import sys
from abc import ABCMeta, abstractmethod
from collections.abc import Awaitable, Callable
from types import TracebackType
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, overload
if sys.version_info >= (3, 11):
    from typing import TypeVarTuple, Unpack
else:
    from typing_extensions import TypeVarTuple, Unpack
if TYPE_CHECKING:
    from .._core._tasks import CancelScope
T_Retval = TypeVar("T_Retval")
T_contra = TypeVar("T_contra", contravariant=True)
PosArgsT = TypeVarTuple("PosArgsT")
class TaskStatus(Protocol[T_contra]):
    @overload
    def started(self: TaskStatus[None]) -> None: ...
    @overload
    def started(self, value: T_contra) -> None: ...
    def started(self, value: T_contra | None = None) -> None:
        """
        Signal that the task has started.
        :param value: object passed back to the starter of the task
        """
    """
    Groups several asynchronous tasks together.
    :ivar cancel_scope: the cancel scope inherited by all child tasks
    :vartype cancel_scope: CancelScope
    .. note:: On asyncio, support for eager task factories is considered to be
        **experimental**. In particular, they don't follow the usual semantics of new
        tasks being scheduled on the next iteration of the event loop, and may thus
        cause unexpected behavior in code that wasn't written with such semantics in
        mind.
    """
        """
        Start a new task in this task group.
        :param func: a coroutine function
        :param args: positional arguments to call the function with
        :param name: name of the task, for the purposes of introspection and debugging
        .. versionadded:: 3.0
        """
        """
        Start a new task and wait until it signals for readiness.
        :param func: a coroutine function
        :param args: positional arguments to call the function with
        :param name: name of the task, for the purposes of introspection and debugging
        :return: the value passed to ``task_status.started()``
        :raises RuntimeError: if the task finishes without calling
            ``task_status.started()``
        .. versionadded:: 3.0
        """
        """Enter the task group context and allow starting new tasks."""
    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
