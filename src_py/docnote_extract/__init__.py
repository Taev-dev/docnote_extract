from docnote import MarkupLang

__all__ = [
    'KNOWN_MARKUP_LANGS',
]

KNOWN_MARKUP_LANGS: set[str | MarkupLang] = set(MarkupLang)
