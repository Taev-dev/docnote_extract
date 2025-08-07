from __future__ import annotations

from collections.abc import Callable

from docnote_extract._extraction import ModulePostExtraction
from docnote_extract._types import Singleton
from docnote_extract.discovery import ModuleTreeNodeHydrated
from docnote_extract.normalization import NormalizedObj

type ModuleObjectFilter = Callable[
    [ModulePostExtraction, dict[str, NormalizedObj]],
    dict[str, NormalizedObj]]
type ObjectFilter = Callable[
    [dict[str, NormalizedObj]], dict[str, NormalizedObj]]


def filter_modules(
        module_tree: ModuleTreeNodeHydrated,
        ) -> ModuleTreeNodeHydrated | None:
    """Recursively walks the passed module tree, filtering out any
    private modules (modules with a relname beginning with an
    underscore, but not ``__dunders__``). Note that this can be
    overwritten by the module's effective config's ``include_in_docs``
    setting, to force the module to be included or skipped.

    Note that this must be applied **after** generating summarizations,
    since there might be re-exports of modules filtered out of the
    result.
    """
    effective_config = module_tree.effective_config

    if (
        effective_config.include_in_docs is False
        or (
            _conventionally_private(module_tree.relname)
            and not effective_config.include_in_docs)
    ):
        return None

    filtered_node = module_tree.clone_without_children()
    for child_name, child_node in module_tree.children.items():
        filtered_child = filter_modules(child_node)
        if filtered_child is not None:
            filtered_node.children[child_name] = filtered_child

    return filtered_node


def filter_module_members(
        module: ModulePostExtraction,
        normalized_objs: dict[str, NormalizedObj],
        *,
        remove_unknown_origins: bool = True
        ) -> dict[str, NormalizedObj]:
    """Given a normalized module ``__dict__``, this filters out all
    entries that cannot be assigned to the passed (canonical)
    ``src_module``.

    Note that seeing a config value for ``include_in_docs`` is not
    relevant to this, for two reasons:
    ++  because it might be an unstubbed (tracked) import, it might
        still be defined somewhere else
    ++  **all of the canonical module inference logic is contained
        within normalization!**
    """
    dunder_all: set[str] = set(getattr(module, '__all__', ()))
    module_name = module.__name__

    retval = {}
    for name, normalized_obj in normalized_objs.items():
        # Dunder all must ALWAYS be included!
        if name in dunder_all:
            retval[name] = normalized_obj
            continue

        canonical_module = normalized_obj.canonical_module
        if canonical_module is Singleton.UNKNOWN:
            if not remove_unknown_origins:
                # Note: remove_unknown_origins=False also applies to the name,
                # so there's no need to check it
                retval[name] = normalized_obj
            continue

        if canonical_module == module_name:
            canonical_name = normalized_obj.canonical_name
            if (
                canonical_name is not None
                and (
                    not remove_unknown_origins
                    or isinstance(canonical_name, str))
            ):
                retval[name] = normalized_obj

    return retval


def filter_inclusion_rules(
        normalized_objs: dict[str, NormalizedObj]
        ) -> dict[str, NormalizedObj]:
    """Given a dict of normalized objects, this applies first the
    normal python conventions (single-underscore names are private),
    and then the effective config for the object, resulting in a final
    decision about whether or not the object should be included in docs
    or not.
    """
    retval: dict[str, NormalizedObj] = {}

    for name, normalized_obj in normalized_objs.items():
        effective_config = normalized_obj.effective_config
        if (
            effective_config.include_in_docs is False
            or (
                _conventionally_private(name)
                and not effective_config.include_in_docs)
        ):
            continue

        retval[name] = normalized_obj

    return retval


def _conventionally_private(name: str) -> bool:
    """Returns True if the passed name is, by python convention, to be
    considered private -- ie, if it starts with an underscore, but isn't
    a dunder.

    Note that this also includes mangled names, since they'll end up
    also starting with an underscore (``Foo.__bar`` is mangled to
    ``Foo._Foo__bar``).
    """
    # Could we do this with regex? Yeah, sure, but then we'd have 3 problems.
    # But more seriously, this is faster to write, faster to read, and -- at
    # least naively -- I would assume it's also a bit faster, since we're not
    # dealing with an entire regex engine.
    return (
        name.startswith('_')
        and not (name.startswith('__') and name.endswith('__')))
