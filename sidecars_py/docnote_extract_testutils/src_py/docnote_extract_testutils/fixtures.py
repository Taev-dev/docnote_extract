import sys


def purge_cached_testpkg_modules(func=None, /):
    """Use this to remove every testpkg module from sys.modules.
    Manually applied to tests for performance reasons.

    Can (optionally) also be applied as a decorator.
    """
    if func is None:
        _do_purge_cached_testpkg_modules()

    else:
        def closure(*args, **kwargs):
            _do_purge_cached_testpkg_modules()
            return func(*args, **kwargs)

        return closure


def _do_purge_cached_testpkg_modules():
    cached_testpkg_modules = [
        module_name for module_name in sys.modules
        if module_name.startswith('docnote_extract_testpkg')]
    for cached_testpkg_module in cached_testpkg_modules:
        # We don't have threading, so the None should be redundant, but we
        # want to be defensive here.
        sys.modules.pop(cached_testpkg_module, None)
