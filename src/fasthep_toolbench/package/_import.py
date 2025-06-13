from __future__ import annotations

import importlib
import inspect
from typing import Any


def is_valid_import(module_path: str, aliases: dict[str, str]) -> bool:
    """Check if a module can be imported."""
    value = aliases.get(module_path, module_path)
    module_path, class_name = value.rsplit(".", 1)
    try:
        # Import the module
        mod = importlib.import_module(module_path)
        # this must be a class
        class_ = getattr(mod, class_name)
        return is_class(class_)
    except ImportError as _:
        return False


def class_from_type_string(type_string: str) -> Any:
    """Get a class from a type string, e.g. 'module.submodule.Class'."""
    module_path, class_name = type_string.rsplit(".", 1)
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


def instance_from_type_string(type_string: str, *args, **kwargs) -> Any:  # type: ignore[no-untyped-def]
    """Create an instance from a type string, e.g. 'module.submodule.Class'."""
    return class_from_type_string(type_string)(*args, **kwargs)


def is_class(obj: Any) -> bool:
    """Check if an object is a class.
    Will unwrap the object to make it work for decorated classes."""
    return inspect.isclass(inspect.unwrap(obj))
