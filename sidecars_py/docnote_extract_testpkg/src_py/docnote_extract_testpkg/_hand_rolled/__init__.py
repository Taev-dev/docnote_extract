# We use this to make sure that the module being inspected doesn't get
# stubs applied to it.
SOME_CONSTANT = 7
SOME_SENTINEL = object()


class ThisGetsUsedToTestNormalization:
    """Normalization needs a class defined within a module that doesn't
    import anything that needs to be stubbed. Here we go!
    """
