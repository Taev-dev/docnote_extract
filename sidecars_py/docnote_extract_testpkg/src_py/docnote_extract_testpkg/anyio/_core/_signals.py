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
from collections.abc import AsyncIterator
from contextlib import AbstractContextManager
from signal import Signals
from ._eventloop import get_async_backend
def open_signal_receiver(
    *signals: Signals,
) -> AbstractContextManager[AsyncIterator[Signals]]:
    """
    Start receiving operating system signals.
    :param signals: signals to receive (e.g. ``signal.SIGINT``)
    :return: an asynchronous context manager for an asynchronous iterator which yields
        signal numbers
    .. warning:: Windows does not support signals natively so it is best to avoid
        relying on this in cross-platform applications.
    .. warning:: On asyncio, this permanently replaces any previous signal handler for
        the given signals, as set via :meth:`~asyncio.loop.add_signal_handler`.
    """
    ...

