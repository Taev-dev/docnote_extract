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
from collections.abc import Awaitable, Generator
from typing import Any, cast
from ._eventloop import get_async_backend
class TaskInfo:
    """
    Represents an asynchronous task.
    :ivar int id: the unique identifier of the task
    :ivar parent_id: the identifier of the parent task, if any
    :vartype parent_id: Optional[int]
    :ivar str name: the description of the task (if any)
    :ivar ~collections.abc.Coroutine coro: the coroutine object of the task
    """
    __slots__ = "_name", "id", "parent_id", "name", "coro"
    def __init__(
        self,
        id: int,
        parent_id: int | None,
        name: str | None,
        coro: Generator[Any, Any, Any] | Awaitable[Any],
    ):
        ...

    def __eq__(self, other: object) -> bool:
        ...

    def __hash__(self) -> int:
        ...

    def __repr__(self) -> str:
        ...

    def has_pending_cancellation(self) -> bool:
        """
        Return ``True`` if the task has a cancellation pending, ``False`` otherwise.
        """
        ...

def get_current_task() -> TaskInfo:
    """
    Return the current task.
    :return: a representation of the current task
    """
    ...

def get_running_tasks() -> list[TaskInfo]:
    """
    Return a list of running tasks in the current event loop.
    :return: a list of task info objects
    """
    ...

async def wait_all_tasks_blocked() -> None:
    """Wait until all other tasks are waiting for something."""
    await get_async_backend().wait_all_tasks_blocked()
