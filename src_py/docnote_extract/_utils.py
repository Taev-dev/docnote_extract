from __future__ import annotations

import typing
from typing import Any
from typing import Literal

from docnote import DOCNOTE_CONFIG_ATTR_FOR_MODULES
from docnote import DocnoteConfig
from docnote import DocnoteConfigParams

from docnote_extract import KNOWN_MARKUP_LANGS
from docnote_extract.exceptions import InvalidConfig

if typing.TYPE_CHECKING:
    from docnote_extract._extraction import ModulePostExtraction


def validate_config(config: DocnoteConfig, hint: Any) -> Literal[True]:
    """Performs any config enforcement (currently, just the
    ``enforce_known_lang`` parameter). Raises ``InvalidConfig`` if
    enforcement fails.
    """
    if config.enforce_known_lang:
        if (
            config.markup_lang is not None
            and config.markup_lang not in KNOWN_MARKUP_LANGS
        ):
            raise InvalidConfig(
                'Unknown markup lang with enforcement enabled!', config, hint)

    return True


def coerce_config(
        module: ModulePostExtraction,
        *,
        parent_stackables: DocnoteConfigParams | None = None
        ) -> DocnoteConfig:
    """Given a module-post-extraction, checks for an explicit config
    defined on the module itself. If found, returns it. If not found,
    creates an empty one.
    """
    explicit_config = getattr(module, DOCNOTE_CONFIG_ATTR_FOR_MODULES, None)
    if parent_stackables is None:
        parent_stackables = {}

    if explicit_config is None:
        return DocnoteConfig(**parent_stackables)

    elif not isinstance(explicit_config, DocnoteConfig):
        raise TypeError(
            f'``<module>.{DOCNOTE_CONFIG_ATTR_FOR_MODULES}`` must always '
            + 'be a ``DocnoteConfig`` instance!', module, explicit_config)

    # Note: the intermediate step is required to OVERWRITE the values. If we
    # just did these directly within ``DocnoteConfig``, python would complain
    # about getting multiple values for the same keyword arg.
    combination: DocnoteConfigParams = {
        **parent_stackables, **explicit_config.as_nontotal_dict()}
    return DocnoteConfig(**combination)
