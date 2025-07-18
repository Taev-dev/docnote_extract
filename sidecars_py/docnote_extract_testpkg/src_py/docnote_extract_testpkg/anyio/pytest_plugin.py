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
import socket
import sys
from collections.abc import Callable, Generator, Iterator
from contextlib import ExitStack, contextmanager
from inspect import isasyncgenfunction, iscoroutinefunction, ismethod
from typing import Any, cast
import pytest
import sniffio
from _pytest.fixtures import SubRequest
from _pytest.outcomes import Exit
from ._core._eventloop import get_all_backends, get_async_backend
from ._core._exceptions import iterate_exceptions
from .abc import TestRunner
if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup
_current_runner: TestRunner | None = None
_runner_stack: ExitStack | None = None
_runner_leases = 0
def extract_backend_and_options(backend: object) -> tuple[str, dict[str, Any]]:
    ...

@contextmanager
def get_runner(
    backend_name: str, backend_options: dict[str, Any]
) -> Iterator[TestRunner]:
    ...

def pytest_configure(config: Any) -> None:
    ...

@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_setup(fixturedef: Any, request: Any) -> Generator[Any]:
    ...

@pytest.hookimpl(tryfirst=True)
def pytest_pycollect_makeitem(collector: Any, name: Any, obj: Any) -> None:
    ...

@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: Any) -> bool | None:
    ...

@pytest.fixture(scope="module", params=get_all_backends())
def anyio_backend(request: Any) -> Any:
    ...

@pytest.fixture
def anyio_backend_name(anyio_backend: Any) -> str:
    ...

@pytest.fixture
def anyio_backend_options(anyio_backend: Any) -> dict[str, Any]:
    ...

class FreePortFactory:
    """
    Manages port generation based on specified socket kind, ensuring no duplicate
    ports are generated.
    This class provides functionality for generating available free ports on the
    system. It is initialized with a specific socket kind and can generate ports
    for given address families while avoiding reuse of previously generated ports.
    Users should not instantiate this class directly, but use the
    ``free_tcp_port_factory`` and ``free_udp_port_factory`` fixtures instead. For simple
    uses cases, ``free_tcp_port`` and ``free_udp_port`` can be used instead.
    """
    def __init__(self, kind: socket.SocketKind) -> None:
        ...

    @property
    def kind(self) -> socket.SocketKind:
        """
        The type of socket connection (e.g., :data:`~socket.SOCK_STREAM` or
        :data:`~socket.SOCK_DGRAM`) used to bind for checking port availability
        """
        ...

    def __call__(self, family: socket.AddressFamily | None = None) -> int:
        """
        Return an unbound port for the given address family.
        :param family: if omitted, both IPv4 and IPv6 addresses will be tried
        :return: a port number
        """
        ...

@pytest.fixture(scope="session")
def free_tcp_port_factory() -> FreePortFactory:
    ...

@pytest.fixture(scope="session")
def free_udp_port_factory() -> FreePortFactory:
    ...

@pytest.fixture
def free_tcp_port(free_tcp_port_factory: Callable[[], int]) -> int:
    ...

@pytest.fixture
def free_udp_port(free_udp_port_factory: Callable[[], int]) -> int:
    ...

