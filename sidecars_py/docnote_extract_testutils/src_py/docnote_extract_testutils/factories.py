from __future__ import annotations

import importlib


def fake_discover_factory(module_names: list[str]):
    """This creates a factory that returns ``discover_all_modules``
    fakes. We need this extra step because the logic in
    ``discover_and_extract`` relies upon ``discover_all_modules``
    actually importing the modules.
    """
    def fake_discover_all_modules(*args, **kwargs):
        retval = {}
        for module_name in module_names:
            retval[module_name] = importlib.import_module(module_name)

        return retval

    return fake_discover_all_modules
