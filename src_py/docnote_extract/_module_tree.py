from __future__ import annotations

import logging
import typing
from dataclasses import KW_ONLY
from dataclasses import dataclass
from dataclasses import field
from dataclasses import fields as dc_fields
from importlib import import_module
from pkgutil import iter_modules
from types import ModuleType
from typing import Any
from typing import Literal
from typing import Self

from docnote import DOCNOTE_CONFIG_ATTR_FOR_MODULES
from docnote import DocnoteConfig
from docnote import DocnoteConfigParams

from docnote_extract import KNOWN_MARKUP_LANGS
from docnote_extract._utils import coerce_config
from docnote_extract._utils import validate_config
from docnote_extract.exceptions import InvalidConfig

if typing.TYPE_CHECKING:
    from docnote_extract._extraction import ModulePostExtraction


@dataclass(slots=True)
class ModuleTreeNode[TN: ModuleTreeNode, TM: ModulePostExtraction | None]:
    """Module trees represent the hierarchy of modules within a package.
    In addition to the module names themselves (and if desired, the
    module objects), they include the effective docnote config for
    every module.

    Note that the existence of the ``effective_config`` is the primary
    reason this class exists; otherwise, a simple string-based tree
    structure would make more sense!
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
                effective_config=coerce_config(root_module),
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
                cfg = coerce_config(submodule, parent_stackables=parent_cfg)
                parent_node.children[relname] = cls(
                    submodule_name,
                    relname,
                    effective_config=cfg,
                    # This is presumably the same problem as above.
                    module=submodule)  # type: ignore

        return roots_by_pkg

    def __truediv__(self, other: str) -> Self:
        return self.children[other]

    def __post_init__(self):
        validate_config(
            self.effective_config, f'Module-level config for {self.fullname}')


type ModuleTreeNodeHydrated = ModuleTreeNode[
    ModuleTreeNodeHydrated, ModulePostExtraction]
type ModuleTreeNodeBare = ModuleTreeNode[ModuleTreeNodeBare, None]
