from __future__ import annotations

import pytest
from docnote import DocnoteConfig
from docnote import MarkupLang
from docnote import Note

from docnote_extract._utils import extract_docstring
from docnote_extract._utils import textify_notes
from docnote_extract._utils import validate_config
from docnote_extract.exceptions import InvalidConfig
from docnote_extract.summaries import DocText


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


class TestTextifyNotes:

    def test_note_without_config(self):
        """Calling on a note that has no config must set the markup
        lang as expected.
        """
        notes = [Note('foo'), Note('bar')]
        config = DocnoteConfig(markup_lang=MarkupLang.RST)

        retval = textify_notes(notes, config)

        assert len(retval) == 2
        assert all(isinstance(textnote, DocText) for textnote in retval)
        assert all(
            textnote.markup_lang is MarkupLang.RST
            for textnote in retval)
        assert {textnote.value for textnote in retval} == {'foo', 'bar'}

    def test_note_with_config(self):
        """Calling on a note that has a config must set the markup
        lang as expected.
        """
        notes = [
            Note('foo'),
            Note(
                'bar',
                config=DocnoteConfig(markup_lang=MarkupLang.CLEANCOPY))]
        config = DocnoteConfig(markup_lang=MarkupLang.RST)

        retval = textify_notes(notes, config)

        assert len(retval) == 2
        doctext1, doctext2 = retval
        assert doctext1.markup_lang is MarkupLang.RST
        assert doctext2.markup_lang is MarkupLang.CLEANCOPY
        assert doctext1.value == 'foo'
        assert doctext2.value == 'bar'


class TestExtractDocstring:

    def test_nonempty(self):
        """Extracting a non-empty docstring must return a DocText
        instance with the markup lang set as per the effective config.
        """
        config = DocnoteConfig(markup_lang=MarkupLang.CLEANCOPY)

        def func():
            """Some docstring
            with 3 lines
            real fancy
            """

        retval = extract_docstring(func, config)

        assert isinstance(retval, DocText)
        assert retval.value == 'Some docstring\nwith 3 lines\nreal fancy'
        assert retval.markup_lang is config.markup_lang

    def test_empty(self):
        """Extracting a whitespace-only docstring must return None."""
        config = DocnoteConfig(markup_lang=MarkupLang.CLEANCOPY)

        def func():
            """   
            
              
            """  # noqa: W291, W293

        retval = extract_docstring(func, config)

        assert retval is None

    def test_nodoc(self):
        """Extracting a non-existent docstring must return None."""
        config = DocnoteConfig(markup_lang=MarkupLang.CLEANCOPY)

        def func(): ...

        retval = extract_docstring(func, config)

        assert retval is None
