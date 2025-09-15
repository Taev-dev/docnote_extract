from __future__ import annotations

from typing import TypeVar


_ModuleTypeVar = TypeVar('_ModuleTypeVar')


def uses_module_typevar(arg: _ModuleTypeVar) -> _ModuleTypeVar: ...


def uses_sugared_typevar[T](arg: T) -> T: ...
