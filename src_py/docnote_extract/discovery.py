"""This module is responsible for the code that explores firstparty
packages to recursively find all their modules.
"""
from __future__ import annotations

import logging
from dataclasses import KW_ONLY
from dataclasses import dataclass
from dataclasses import field
from importlib import import_module
from pkgutil import walk_packages
from types import ModuleType

from docnote import DocnoteConfig

logger = logging.getLogger(__name__)


def discover_all_modules(
        *root_packages: str
        ) -> dict[str, ModuleType]:
    """Recursively imports all of the modules under the passed
    ``root_packages``. Returns the loaded modules.
    """
    retval = {}
    for root_package in root_packages:
        root_module = retval[root_package] = import_module(root_package)
        eager_import_submodules(root_module, loaded_modules=retval)

    return retval


def eager_import_submodules(
        module: ModuleType,
        *,
        # This is purely here for the purposes of making the recursion more
        # efficient by avoiding repeated dict merges
        loaded_modules: dict[str, ModuleType]
        ) -> dict[str, ModuleType]:
    """This recursively imports all of the submodules of the passed
    module. It returns a mapping of the full module name to its loaded
    module.

    Note that, as per stdlib docs on ``walk_packages``, this relies upon
    the package finder supporting ``iter_modules()``, and is therefore
    sensitive to the current status of our import hook:

    >
    __embed__: 'text/quote'
        Only works for a finder which defines an iter_modules() method.
        This interface is non-standard, so the module also provides
        implementations for importlib.machinery.FileFinder and
        zipimport.zipimporter.

    Also note that **this does not support namespace packages.** This is
    a limitation of cpython; the only workarounds would be to eagerly
    explore every single subfolder within a python package. This might
    be desirable in some cases, but in others, it's a mess.
    """
    # Note that this is the whole absolute name and not the relative path.
    parent_package_name = module.__name__

    # Note: all packages are modules (in this context), but not all modules
    # are packages. In other words: packages have submodules, but if
    # is_package is falsy, then it doesn't. That's literally its meaning
    # here.
    recurseable_pkg_modules = set()

    # Theoretically walk_packages should be recursive, but in practice it
    # appears to always require an ``__init__.py``, despite this not being
    # the python spec.
    # https://stackoverflow.com/questions/3365740/
    # https://stackoverflow.com/questions/17024605/
    for __, submodule_name_rel, is_package in walk_packages(module.__path__):
        submodule_name_abs = f'{parent_package_name}.{submodule_name_rel}'

        try:
            submodule = import_module(submodule_name_abs)
        except ModuleNotFoundError:
            logger.exception(
                'Failed to import submodule %s; skipping', submodule_name_abs)
            continue

        loaded_modules[submodule_name_abs] = submodule

        if is_package:
            recurseable_pkg_modules.add(submodule)

    # Separating this from the above for loop does insulates us from the actual
    # behavior of walk_packages in two ways. First, it deduplicates the modules
    # into a set, so we can skip over any duplicate loads. Second, it lets us
    # compare the values with the already loaded modules, and skip them if they
    # were already loaded.
    for recurseable_pkg_module in recurseable_pkg_modules:
        if recurseable_pkg_module not in loaded_modules:
            eager_import_submodules(
                recurseable_pkg_module,
                loaded_modules=loaded_modules)

    return loaded_modules


@dataclass(slots=True)
class ModuleTreeNode:
    """Module trees represent the hierarchy of modules within a package.
    In addition to the module names themselves (and if desired, the
    module objects), they include the effective docnote config for
    every module.
    """
    fullname: str
    relname: str
    children: dict[str, ModuleTreeNode] = field(default_factory=dict)

    _: KW_ONLY
    effective_config: DocnoteConfig = field(compare=False, repr=False)
    module: ModuleType | None = field(default=None, compare=False, repr=False)

    def find(self, name: str):
        """Finds the node associated with the passed module name.
        Intended to be used from the module root, with absolute names,
        but also generally usable to traverse into child nodes.
        """
        relname_segments = name.split('.')
        if self.relname != relname_segments[0]:
            raise ValueError(
                'Find must start with the current node! Path not in tree.',
                self.relname, name)

        node = self
        for relname in relname_segments[1:]:
            try:
                node = node.children[relname]
            except KeyError as exc:
                exc.add_note(
                    f'Module {name} not found within in package/module '
                    + self.fullname)
                raise exc

        return node
