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
import errno
import socket
import sys
from abc import abstractmethod
from collections.abc import Callable, Collection, Mapping
from contextlib import AsyncExitStack
from io import IOBase
from ipaddress import IPv4Address, IPv6Address
from socket import AddressFamily
from typing import Any, TypeVar, Union
from .._core._eventloop import get_async_backend
from .._core._typedattr import (
    TypedAttributeProvider,
    TypedAttributeSet,
    typed_attribute,
)
from ._streams import ByteStream, Listener, UnreliableObjectStream
from ._tasks import TaskGroup
if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias
IPAddressType: TypeAlias = Union[str, IPv4Address, IPv6Address]
IPSockAddrType: TypeAlias = tuple[str, int]
SockAddrType: TypeAlias = Union[IPSockAddrType, str]
UDPPacketType: TypeAlias = tuple[bytes, IPSockAddrType]
UNIXDatagramPacketType: TypeAlias = tuple[bytes, str]
T_Retval = TypeVar("T_Retval")
def _validate_socket(
    sock_or_fd: socket.socket | int,
    sock_type: socket.SocketKind,
    addr_family: socket.AddressFamily = socket.AF_UNSPEC,
    *,
    require_connected: bool = False,
    require_bound: bool = False,
) -> socket.socket:
    ...

class SocketAttribute(TypedAttributeSet):
    family: AddressFamily = typed_attribute()
    local_address: SockAddrType = typed_attribute()
    local_port: int = typed_attribute()
    raw_socket: socket.socket = typed_attribute()
    remote_address: SockAddrType = typed_attribute()
    remote_port: int = typed_attribute()
class _SocketProvider(TypedAttributeProvider):
    @property
    def extra_attributes(self) -> Mapping[Any, Callable[[], Any]]:
        ...

    @property
    @abstractmethod
    def _raw_socket(self) -> socket.socket:
        ...

class SocketStream(ByteStream, _SocketProvider):
    """
    Transports bytes over a socket.
    Supports all relevant extra attributes from :class:`~SocketAttribute`.
    """
    @classmethod
    async def from_socket(cls, sock_or_fd: socket.socket | int) -> SocketStream:
        """
        Wrap an existing socket object or file descriptor as a socket stream.
        The newly created socket wrapper takes ownership of the socket being passed in.
        The existing socket must already be connected.
        :param sock_or_fd: a socket object or file descriptor
        :return: a socket stream
        """
        sock = _validate_socket(sock_or_fd, socket.SOCK_STREAM, require_connected=True)
        return await get_async_backend().wrap_stream_socket(sock)
class UNIXSocketStream(SocketStream):
    @classmethod
    async def from_socket(cls, sock_or_fd: socket.socket | int) -> UNIXSocketStream:
        """
        Wrap an existing socket object or file descriptor as a UNIX socket stream.
        The newly created socket wrapper takes ownership of the socket being passed in.
        The existing socket must already be connected.
        :param sock_or_fd: a socket object or file descriptor
        :return: a UNIX socket stream
        """
        sock = _validate_socket(
            sock_or_fd, socket.SOCK_STREAM, socket.AF_UNIX, require_connected=True
        )
        return await get_async_backend().wrap_unix_stream_socket(sock)
    @abstractmethod
    async def send_fds(self, message: bytes, fds: Collection[int | IOBase]) -> None:
        """
        Send file descriptors along with a message to the peer.
        :param message: a non-empty bytestring
        :param fds: a collection of files (either numeric file descriptors or open file
            or socket objects)
        """
    @abstractmethod
    async def receive_fds(self, msglen: int, maxfds: int) -> tuple[bytes, list[int]]:
        """
        Receive file descriptors along with a message from the peer.
        :param msglen: length of the message to expect from the peer
        :param maxfds: maximum number of file descriptors to expect from the peer
        :return: a tuple of (message, file descriptors)
        """
class SocketListener(Listener[SocketStream], _SocketProvider):
    """
    Listens to incoming socket connections.
    Supports all relevant extra attributes from :class:`~SocketAttribute`.
    """
    @classmethod
    async def from_socket(
        cls,
        sock_or_fd: socket.socket | int,
    ) -> SocketListener:
        """
        Wrap an existing socket object or file descriptor as a socket listener.
        The newly created listener takes ownership of the socket being passed in.
        :param sock_or_fd: a socket object or file descriptor
        :return: a socket listener
        """
        sock = _validate_socket(sock_or_fd, socket.SOCK_STREAM, require_bound=True)
        return await get_async_backend().wrap_listener_socket(sock)
    @abstractmethod
    async def accept(self) -> SocketStream:
        """Accept an incoming connection."""
    async def serve(
        self,
        handler: Callable[[SocketStream], Any],
        task_group: TaskGroup | None = None,
    ) -> None:
        from .. import create_task_group
        async with AsyncExitStack() as stack:
            if task_group is None:
                task_group = await stack.enter_async_context(create_task_group())
            while True:
                stream = await self.accept()
                task_group.start_soon(handler, stream)
class UDPSocket(UnreliableObjectStream[UDPPacketType], _SocketProvider):
    """
    Represents an unconnected UDP socket.
    Supports all relevant extra attributes from :class:`~SocketAttribute`.
    """
    @classmethod
    async def from_socket(cls, sock_or_fd: socket.socket | int) -> UDPSocket:
        """
        Wrap an existing socket object or file descriptor as a UDP socket.
        The newly created socket wrapper takes ownership of the socket being passed in.
        The existing socket must be bound to a local address.
        :param sock_or_fd: a socket object or file descriptor
        :return: a UDP socket
        """
        sock = _validate_socket(sock_or_fd, socket.SOCK_DGRAM, require_bound=True)
        return await get_async_backend().wrap_udp_socket(sock)
    async def sendto(self, data: bytes, host: str, port: int) -> None:
        """
        Alias for :meth:`~.UnreliableObjectSendStream.send` ((data, (host, port))).
        """
        return await self.send((data, (host, port)))
class ConnectedUDPSocket(UnreliableObjectStream[bytes], _SocketProvider):
    """
    Represents an connected UDP socket.
    Supports all relevant extra attributes from :class:`~SocketAttribute`.
    """
    @classmethod
    async def from_socket(cls, sock_or_fd: socket.socket | int) -> ConnectedUDPSocket:
        """
        Wrap an existing socket object or file descriptor as a connected UDP socket.
        The newly created socket wrapper takes ownership of the socket being passed in.
        The existing socket must already be connected.
        :param sock_or_fd: a socket object or file descriptor
        :return: a connected UDP socket
        """
        sock = _validate_socket(
            sock_or_fd,
            socket.SOCK_DGRAM,
            require_connected=True,
        )
        return await get_async_backend().wrap_connected_udp_socket(sock)
class UNIXDatagramSocket(
    UnreliableObjectStream[UNIXDatagramPacketType], _SocketProvider
):
    """
    Represents an unconnected Unix datagram socket.
    Supports all relevant extra attributes from :class:`~SocketAttribute`.
    """
    @classmethod
    async def from_socket(
        cls,
        sock_or_fd: socket.socket | int,
    ) -> UNIXDatagramSocket:
        """
        Wrap an existing socket object or file descriptor as a UNIX datagram
        socket.
        The newly created socket wrapper takes ownership of the socket being passed in.
        :param sock_or_fd: a socket object or file descriptor
        :return: a UNIX datagram socket
        """
        sock = _validate_socket(sock_or_fd, socket.SOCK_DGRAM, socket.AF_UNIX)
        return await get_async_backend().wrap_unix_datagram_socket(sock)
    async def sendto(self, data: bytes, path: str) -> None:
        """Alias for :meth:`~.UnreliableObjectSendStream.send` ((data, path))."""
        return await self.send((data, path))
class ConnectedUNIXDatagramSocket(UnreliableObjectStream[bytes], _SocketProvider):
    """
    Represents a connected Unix datagram socket.
    Supports all relevant extra attributes from :class:`~SocketAttribute`.
    """
    @classmethod
    async def from_socket(
        cls,
        sock_or_fd: socket.socket | int,
    ) -> ConnectedUNIXDatagramSocket:
        """
        Wrap an existing socket object or file descriptor as a connected UNIX datagram
        socket.
        The newly created socket wrapper takes ownership of the socket being passed in.
        The existing socket must already be connected.
        :param sock_or_fd: a socket object or file descriptor
        :return: a connected UNIX datagram socket
        """
        sock = _validate_socket(
            sock_or_fd, socket.SOCK_DGRAM, socket.AF_UNIX, require_connected=True
        )
        return await get_async_backend().wrap_connected_unix_datagram_socket(sock)
