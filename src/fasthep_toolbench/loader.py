from __future__ import annotations

import importlib
from collections.abc import Mapping
from typing import Any

from fasthep_toolbench.model import ToolBinding, ToolSpec
from fasthep_toolbench.registry import resolve_tool_registry_config


def load_object(ref: str) -> Any:
    """Load an object from a 'module.submodule:object' reference."""
    if ":" not in ref:
        msg = f"Invalid object spec '{ref}'. Expected format 'module.submodule:object'"
        raise ValueError(msg)
    module_name, object_name = ref.split(":", 1)
    module = importlib.import_module(module_name)
    try:
        return getattr(module, object_name)
    except AttributeError as exc:
        msg = f"Module '{module_name}' has no attribute '{object_name}'"
        raise AttributeError(msg) from exc


def list_registered_tools(
    registry_cfg: Mapping[str, Any] | None = None,
    *,
    include_entry_points: bool = True,
) -> list[str]:
    registry = resolve_tool_registry_config(
        registry_cfg,
        include_entry_points=include_entry_points,
    )
    tools = registry.get("tools", {})
    if not isinstance(tools, Mapping):
        msg = "Tool registry section 'tools' must be a mapping"
        raise TypeError(msg)
    return sorted(str(name) for name in tools)


def load_tool_entry(
    name: str,
    registry_cfg: Mapping[str, Any] | None = None,
    *,
    include_entry_points: bool = True,
) -> Mapping[str, Any]:
    registry = resolve_tool_registry_config(
        registry_cfg,
        include_entry_points=include_entry_points,
    )
    tools = registry.get("tools", {})
    if not isinstance(tools, Mapping):
        msg = "Tool registry section 'tools' must be a mapping"
        raise TypeError(msg)
    try:
        entry = tools[name]
    except KeyError as exc:
        msg = f"Unknown tool registry entry '{name}'"
        raise KeyError(msg) from exc
    if not isinstance(entry, Mapping):
        msg = f"Tool registry entry '{name}' must be a mapping"
        raise TypeError(msg)
    return entry


def load_tool_binding(
    name: str,
    registry_cfg: Mapping[str, Any] | None = None,
    *,
    include_entry_points: bool = True,
) -> ToolBinding:
    """Resolve registry references and validate the raw tool spec."""
    entry = load_tool_entry(
        name,
        registry_cfg,
        include_entry_points=include_entry_points,
    )
    try:
        spec_ref = entry["spec"]
        impl_ref = entry["impl"]
    except KeyError as exc:
        msg = f"Tool registry entry '{name}' must define 'spec' and 'impl'"
        raise KeyError(msg) from exc
    spec = ToolSpec.from_obj(load_object(spec_ref))
    impl = load_object(impl_ref)
    if not callable(impl):
        msg = f"Tool implementation '{name}' must be callable"
        raise TypeError(msg)
    return ToolBinding(name=name, spec=spec, impl=impl, entry=entry)
