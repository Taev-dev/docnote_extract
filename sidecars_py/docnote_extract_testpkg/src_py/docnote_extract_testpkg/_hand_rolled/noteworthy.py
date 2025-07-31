"""This contains notes and configs for testing normalization.
"""
from collections.abc import Callable
from functools import partial
from typing import Annotated

from docnote import DocnoteConfig
from docnote import MarkupLang
from docnote import Note
from docnote import docnote


ClcNote: Annotated[
        Callable[[str], Note],
        DocnoteConfig(include_in_docs=False)
    ] = partial(Note, config=DocnoteConfig(markup_lang=MarkupLang.CLEANCOPY))
DOCNOTE_CONFIG_ATTR: Annotated[
        str,
        Note('''Docs generation libraries should use this value to
            get access to any configs attached to objects via the
            ``docnote`` decorator.
            ''')
    ] = '_docnote_config'


@docnote(DocnoteConfig(include_in_docs=False))
def func_with_config():
    """This is here just to make sure that normalization works when a
    config is attached via the ``@docnote`` decorator instead of an
    annotation.
    """
