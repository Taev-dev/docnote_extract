# This is a programmatically-vendored code sample
# that has been stubbified (ie, function bodies removed). Do not modify
# it directly; your changes will just be overwritten.

# The original source is:
# PkgSrcSpec(forge='github',
#            repo_id='agronholm/anyio',
#            pkg_name='anyio',
#            offset_dest_root_dir=None,
#            root_path='src/anyio',
#            commit_hash='65fe287039e2ded48752e1111a82c29d07725e36',
#            license_paths={'LICENSE'})

# The license of the original project is included in the top level of
# the vendored project directory.

# To regenerate, see sidecars/docnote_extract_testpkg_factory. The
# command is:
# ``uv run python -m docnote_extract_testpkg_factory``.

from __future__ import annotations
from collections.abc import Callable, Mapping
from typing import Any, TypeVar, final, overload
from ._exceptions import TypedAttributeLookupError
T_Attr = TypeVar("T_Attr")
T_Default = TypeVar("T_Default")
undefined = object()
def typed_attribute() -> Any:
    """Return a unique object, used to mark typed attributes."""
    return object()
class TypedAttributeSet:
    """
    """
    def __init_subclass__(cls) -> None:
        annotations: dict[str, Any] = getattr(cls, "__annotations__", {})
        for attrname in dir(cls):
            if not attrname.startswith("_") and attrname not in annotations:
                raise TypeError(
                    f"Attribute {attrname!r} is missing its type annotation"
                )
        super().__init_subclass__()
class TypedAttributeProvider:
    ...

    """Base class for classes that wish to provide typed extra attributes."""
    @property
    def extra_attributes(self) -> Mapping[T_Attr, Callable[[], T_Attr]]:
        """
        A mapping of the extra attributes to callables that return the corresponding
        values.
        If the provider wraps another provider, the attributes from that wrapper should
        also be included in the returned mapping (but the wrapper may override the
        callables from the wrapped instance).
        """
        ...

    @overload
    def extra(self, attribute: T_Attr) -> T_Attr: ...
    @overload
    def extra(self, attribute: T_Attr, default: T_Default) -> T_Attr | T_Default: ...
    @final
    def extra(self, attribute: Any, default: object = undefined) -> object:
        """
        extra(attribute, default=undefined)
        Return the value of the given typed extra attribute.
        :param attribute: the attribute (member of a :class:`~TypedAttributeSet`) to
            look for
        :param default: the value that should be returned if no value is found for the
            attribute
        :raises ~anyio.TypedAttributeLookupError: if the search failed and no default
            value was given
        """
        ...

