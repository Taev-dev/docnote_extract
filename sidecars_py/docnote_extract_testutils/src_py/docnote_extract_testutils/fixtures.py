import sys
from collections.abc import Callable
from contextlib import contextmanager
from functools import wraps
from typing import overload

from docnote_extract._extraction import _EXTRACTION_PHASE
from docnote_extract._extraction import _MODULE_TO_INSPECT
from docnote_extract._extraction import _ExtractionPhase


@overload
def purge_cached_testpkg_modules() -> None: ...
@overload
def purge_cached_testpkg_modules[T: Callable](func: T, /) -> T: ...
def purge_cached_testpkg_modules[T: Callable](
        func : T | None = None, /) -> T | None:
    """Use this to remove every testpkg module from sys.modules.
    Manually applied to tests for performance reasons.

    Can (optionally) also be applied as a decorator.
    """
    if func is None:
        _do_purge_cached_testpkg_modules()

    else:
        @wraps(func)
        def closure(*args, **kwargs):
            _do_purge_cached_testpkg_modules()
            return func(*args, **kwargs)

        return closure  # type: ignore


def _do_purge_cached_testpkg_modules():
    cached_testpkg_modules = [
        module_name for module_name in sys.modules
        if module_name.startswith('docnote_extract_testpkg')]
    for cached_testpkg_module in cached_testpkg_modules:
        # We don't have threading, so the None should be redundant, but we
        # want to be defensive here.
        sys.modules.pop(cached_testpkg_module, None)


@contextmanager
def set_phase(phase: _ExtractionPhase):
    ctx_token = _EXTRACTION_PHASE.set(phase)
    try:
        yield
    finally:
        _EXTRACTION_PHASE.reset(ctx_token)


@contextmanager
def set_inspection(module: str):
    ctx_token = _MODULE_TO_INSPECT.set(module)
    try:
        yield
    finally:
        _MODULE_TO_INSPECT.reset(ctx_token)
