"""This module is responsible for the code that explores firstparty
packages to recursively find all their modules.
"""
from __future__ import annotations

import logging
import typing
from dataclasses import KW_ONLY
from dataclasses import dataclass
from dataclasses import field
from dataclasses import fields as dc_fields
from importlib import import_module
from pkgutil import walk_packages
from types import ModuleType
from typing import Self

from docnote import DocnoteConfig
from docnote import DocnoteConfigParams

if typing.TYPE_CHECKING:
    from docnote_extract._extraction import ModulePostExtraction

logger = logging.getLogger(__name__)

MODULE_DOCNOTE_CONFIG_ATTR = 'DOCNOTE_CONFIG'


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
class ModuleTreeNode[TN: ModuleTreeNode, TM: ModulePostExtraction | None]:
    """Module trees represent the hierarchy of modules within a package.
    In addition to the module names themselves (and if desired, the
    module objects), they include the effective docnote config for
    every module.
    """
    fullname: str
    relname: str
    children: dict[str, Self] = field(default_factory=dict)

    _: KW_ONLY
    effective_config: DocnoteConfig = field(compare=False, repr=False)
    # Pyright appears to have a bug with the generic None not matching the
    # explicit None in the default
    module: TM = field(default=None, compare=False, repr=False)  # type: ignore

    def find(self, name: str) -> Self:
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

    def clone_without_children(self) -> Self:
        """Creates a copy of the current node, except without any
        children. Useful when you need to create a copy of the tree
        while filtering some children out.
        """
        params = {}
        for field_obj in dc_fields(self):
            if field_obj.name != 'children':
                params[field_obj.name] = getattr(self, field_obj.name)

        return type(self)(**params)

    def flatten(
            self,
            *,
            _flattened: dict[str, TM] | None = None
            ) -> dict[str, TM]:
        """Converts the tree (back) into a flattened dictionary with
        all nodes expressed by their fullname. If this is a bare tree
        (ie, there are no modules), all of the values will be ``None``.
        """
        if _flattened is None:
            _flattened = {}

        _flattened[self.fullname] = self.module
        for child in self.children.values():
            child.flatten(_flattened=_flattened)

        return _flattened

    @classmethod
    def from_extraction(
            cls,
            extraction: dict[str, ModulePostExtraction]
            ) -> dict[str, ModuleTreeNodeHydrated]:
        """Given the results of
        ``_ExtractionFinderLoader.discover_and_extract`` -- namely, a
        dict of ``{module_fullname: ModulePostExtraction}`` -- construct
        a new ``ModuleTreeNode`` for each of the firstparty modules
        contained in the extraction.
        """
        max_depth = max(module_name.count('.') for module_name in extraction)
        # We're going to sort all of the modules based on how deep their
        # names are. We can then use this to make sure that the parent is
        # fully defined before continuing on to the children, making it easier
        # to construct the effective config.
        depth_stack: list[dict[str, ModulePostExtraction]] = [
            {} for _ in range(max_depth + 1)]
        for module_name, module in extraction.items():
            depth_stack[module_name.count('.')][module_name] = module

        roots_by_pkg: dict[str, ModuleTreeNode] = {}
        for package_name, root_module in depth_stack[0].items():
            roots_by_pkg[package_name] = cls(
                fullname=package_name,
                relname=package_name,
                effective_config=_coerce_config(root_module),
                # I'm not sure if this is a pyright bug related to recursive
                # generics, or if it's PEBKAC, but either way: ignoring is the
                # most pragmatic resolution.
                module=root_module)  # type: ignore

        for submodule_depth in depth_stack[1:]:
            for submodule_name, submodule in submodule_depth.items():
                root_pkg_name, *_, relname = submodule_name.split('.')
                parent_module_name, _, _ = submodule_name.rpartition('.')
                root_node = roots_by_pkg[root_pkg_name]
                parent_node = root_node.find(parent_module_name)
                parent_cfg = parent_node.effective_config.get_stackables()
                cfg = _coerce_config(submodule, parent_stackables=parent_cfg)
                parent_node.children[relname] = cls(
                    submodule_name,
                    relname,
                    effective_config=cfg,
                    # This is presumably the same problem as above.
                    module=submodule)  # type: ignore

        return roots_by_pkg

    def __truediv__(self, other: str) -> Self:
        return self.children[other]


type ModuleTreeNodeHydrated = ModuleTreeNode[
    ModuleTreeNodeHydrated, ModulePostExtraction]
type ModuleTreeNodeBare = ModuleTreeNode[ModuleTreeNodeBare, None]


def _coerce_config(
        module: ModulePostExtraction,
        *,
        parent_stackables: DocnoteConfigParams | None = None
        ) -> DocnoteConfig:
    """Given a module-post-extraction, checks for an explicit config
    defined on the module itself. If found, returns it. If not found,
    creates an empty one.
    """
    explicit_config = getattr(module, MODULE_DOCNOTE_CONFIG_ATTR, None)
    if parent_stackables is None:
        parent_stackables = {}

    if explicit_config is None:
        return DocnoteConfig(**parent_stackables)

    elif not isinstance(explicit_config, DocnoteConfig):
        raise TypeError(
            f'``<module>.{MODULE_DOCNOTE_CONFIG_ATTR}`` must always '
            + 'be a ``DocnoteConfig`` instance!', module, explicit_config)

    # Note: the intermediate step is required to OVERWRITE the values. If we
    # just did these directly within ``DocnoteConfig``, python would complain
    # about getting multiple values for the same keyword arg.
    combination: DocnoteConfigParams = {
        **parent_stackables, **explicit_config.as_nontotal_dict()}
    return DocnoteConfig(**combination)
