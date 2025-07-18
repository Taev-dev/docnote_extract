import importlib
import sys
import typing
from collections.abc import Generator
from collections.abc import Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from importlib.abc import Loader
from importlib.machinery import ModuleSpec
from types import ModuleType
from unittest.mock import MagicMock

THIRDPARTY_BYPASS_PACKAGES = {
    'docnote',
    'docnote_extract',
}

_MODULE_TO_INSPECT: ContextVar[str] = ContextVar('_MODULE_TO_INSPECT')


@contextmanager
def inspect_module(module_name: str) -> Generator[ModuleType, None, None]:
    """This contextmanager ensures that you get a normal module instance
    for the ``module_name`` you want to inspect, while all other
    non-bypassed, non-stdlib modules are passed through the import hook.

    Note that the module name here must be an EXACT module fullname.
    This doesn't work for entire packages (deliberately!), it only does
    singular modules.
    """
    if _MODULE_TO_INSPECT.get(None) is not None:
        raise RuntimeError('inspect_module is not reentrant!', module_name)

    reset_token = _MODULE_TO_INSPECT.set(module_name)
    try:
        # This allows us to also get references hidden behind circular imports
        typing.TYPE_CHECKING = True
        # This means we have a hooked/stubbed version of the library already
        # present, and we need to reload it.
        # Note that as per stdlib docs, mucking with sys.modules directly is
        # a bad idea, so we'll allow importlib to do the dirty work for us.
        if module_name in sys.modules:
            real_fake_module = importlib.reload(sys.modules['module_name'])
        # In this case, we don't have a hooked/stubbed version of the library,
        # but we still need to load it in the first place.
        else:
            real_fake_module = importlib.import_module(module_name)

        try:
            yield real_fake_module

        # To avoid cross-pollination, we want to make sure that we don't keep
        # the real_fake version of the module around in sys modules, since
        # the next module to be inspected won't then get our reference proxies,
        # but rather, actual objects.
        finally:
            typing.TYPE_CHECKING = False
            # Note that this is necessary to un-bypass the import hook.
            # We could structure this differently, probably with an exitstack,
            # but the logic would be way more complicated to follow. This is
            # an easy and understandable workaround.
            _MODULE_TO_INSPECT.set('')
            importlib.reload(real_fake_module)

    finally:
        _MODULE_TO_INSPECT.reset(reset_token)


class LoadStubMockingModule(Loader):
    """This is an import loader that creates a normal module object and
    populates its __getattr__ with a function that simply returns a
    Mock object.

    This is useful to be able to use importlib.import_library on a
    source file without having any of its upstream dependencies
    installed.
    """

    def find_spec(
            self,
            fullname: str,
            path: Sequence[str] | None,
            target: ModuleType | None = None
            ) -> ModuleSpec | None:
        """We use find_spec to filter which packages we're going to
        install the import hook for, and which we aren't.
        """
        base_package, *_ = fullname.split('.')
        if (
            base_package in sys.stdlib_module_names
            or base_package in THIRDPARTY_BYPASS_PACKAGES
        ):
            return None

        # This is how we bypass our loader for individual modules that we want
        # to inspect
        current_target_module = _MODULE_TO_INSPECT.get(None)
        if current_target_module is None or current_target_module != fullname:
            return ModuleSpec(fullname, self)
        else:
            return None

    def create_module(self, spec: ModuleSpec) -> None | ModuleType:
        return None

    def exec_module(self, module: ModuleType):
        """The import system creates a module object for us; in
        ``exec_module``, it's our job to populate the module with its
        namespace.

        However, instead of populating the module with actual objects,
        we'll just give it a MODULE ``__getattr__`` that creates proxy
        objects on the fly.
        """
        module.__dict__['__getattr__'] = lambda name: MagicMock()
        print(f'exec_module called for {module.__name__}')


def install_import_hook():
    sys.meta_path.append(LoadStubMockingModule())
