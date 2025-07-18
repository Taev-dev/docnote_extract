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
from abc import abstractmethod
from signal import Signals
from ._resources import AsyncResource
from ._streams import ByteReceiveStream, ByteSendStream
class Process(AsyncResource):
    """An asynchronous version of :class:`subprocess.Popen`."""
    @abstractmethod
    async def wait(self) -> int:
        """
        Wait until the process exits.
        :return: the exit code of the process
        """
    @abstractmethod
    def terminate(self) -> None:
        """
        Terminates the process, gracefully if possible.
        On Windows, this calls ``TerminateProcess()``.
        On POSIX systems, this sends ``SIGTERM`` to the process.
        .. seealso:: :meth:`subprocess.Popen.terminate`
        """
        ...

    @abstractmethod
    def kill(self) -> None:
        """
        Kills the process.
        On Windows, this calls ``TerminateProcess()``.
        On POSIX systems, this sends ``SIGKILL`` to the process.
        .. seealso:: :meth:`subprocess.Popen.kill`
        """
        ...

    @abstractmethod
    def send_signal(self, signal: Signals) -> None:
        """
        Send a signal to the subprocess.
        .. seealso:: :meth:`subprocess.Popen.send_signal`
        :param signal: the signal number (e.g. :data:`signal.SIGHUP`)
        """
        ...

    @property
    @abstractmethod
    def pid(self) -> int:
        """The process ID of the process."""
    @property
    @abstractmethod
    def returncode(self) -> int | None:
        """
        ...

    @property
    @abstractmethod
    def stdin(self) -> ByteSendStream | None:
        """The stream for the standard input of the process."""
    @property
    @abstractmethod
    def stdout(self) -> ByteReceiveStream | None:
        """The stream for the standard output of the process."""
        ...

    @property
    @abstractmethod
    def stderr(self) -> ByteReceiveStream | None:
        """The stream for the standard error output of the process."""
