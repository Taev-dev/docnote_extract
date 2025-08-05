class InvalidConfig(Exception):
    """Raised when ``DocnoteConfig`` validation fails. Currently, this
    only applies if ``enforce_known_lang`` was set to True, but the
    declared ``markup_lang`` was unknown.
    """
