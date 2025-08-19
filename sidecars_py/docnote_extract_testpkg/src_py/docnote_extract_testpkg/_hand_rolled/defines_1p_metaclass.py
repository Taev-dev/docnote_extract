from docnote import DocnoteConfig
from docnote import ReftypeMarker
from docnote import docnote


@docnote(DocnoteConfig(mark_special_reftype=ReftypeMarker.METACLASS))
class Mcls1p(type):
    """Just an arbitrary firstparty metaclass."""
