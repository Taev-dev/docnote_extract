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
import math
from typing import TypeVar
from warnings import warn
from ..streams.memory import (
    MemoryObjectReceiveStream,
    MemoryObjectSendStream,
    MemoryObjectStreamState,
)
T_Item = TypeVar("T_Item")
class create_memory_object_stream(
    tuple[MemoryObjectSendStream[T_Item], MemoryObjectReceiveStream[T_Item]],
):
    """
    Create a memory object stream.
    The stream's item type can be annotated like
    :func:`create_memory_object_stream[T_Item]`.
    :param max_buffer_size: number of items held in the buffer until ``send()`` starts
        blocking
    :param item_type: old way of marking the streams with the right generic type for
        static typing (does nothing on AnyIO 4)
        .. deprecated:: 4.0
          Use ``create_memory_object_stream[YourItemType](...)`` instead.
    :return: a tuple of (send stream, receive stream)
    """
    def __new__(  
        cls, max_buffer_size: float = 0, item_type: object = None
    ) -> tuple[MemoryObjectSendStream[T_Item], MemoryObjectReceiveStream[T_Item]]:
        ...

