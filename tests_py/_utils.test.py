from __future__ import annotations

import pytest
from docnote import DocnoteConfig
from docnote import MarkupLang

from docnote_extract._utils import validate_config
from docnote_extract.exceptions import InvalidConfig


class TestValidateConfig:

    def test_no_enforcement(self):
        """A config with no enforcement set must return True."""
        config = DocnoteConfig(enforce_known_lang=False, markup_lang='foobar')
        assert validate_config(config, None) is True

    def test_valid(self):
        """A valid config must return True."""
        config = DocnoteConfig(
            enforce_known_lang=True,
            markup_lang=MarkupLang.CLEANCOPY)
        assert validate_config(config, None) is True

    def test_invalid(self):
        """An invalid config must raise InvalidConfig."""
        config = DocnoteConfig(
            enforce_known_lang=True,
            markup_lang='foobar')

        with pytest.raises(InvalidConfig):
            validate_config(config, None)
