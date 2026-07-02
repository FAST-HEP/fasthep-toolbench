from __future__ import annotations

import inspect
from collections.abc import Mapping, Sequence
from typing import Any

from fasthep_toolbench.args import parse_tool_args
from fasthep_toolbench.availability import tool_availability
from fasthep_toolbench.loader import list_registered_tools as _list_registered_tools
from fasthep_toolbench.loader import load_tool_binding


def list_registered_tools(
    registry_cfg: Mapping[str, Any] | None = None,
    *,
    include_entry_points: bool = True,
) -> list[str]:
    return _list_registered_tools(
        registry_cfg,
        include_entry_points=include_entry_points,
    )


def run_registered_tool(
    name: str,
    args: Sequence[str] | None = None,
    registry_cfg: Mapping[str, Any] | None = None,
    *,
    include_entry_points: bool = True,
) -> Any:
    binding = load_tool_binding(
        name,
        registry_cfg,
        include_entry_points=include_entry_points,
    )
    params = parse_tool_args(binding.spec, list(args or []))
    availability = tool_availability(binding.spec)
    signature = inspect.signature(binding.impl)
    if "availability" in signature.parameters:
        return binding.impl(**params, availability=availability)
    return binding.impl(**params)


def tool_info(
    name: str,
    registry_cfg: Mapping[str, Any] | None = None,
    *,
    include_entry_points: bool = True,
) -> dict[str, Any]:
    binding = load_tool_binding(
        name,
        registry_cfg,
        include_entry_points=include_entry_points,
    )
    availability = tool_availability(binding.spec)
    return {
        "name": name,
        "spec": binding.spec,
        "registry": dict(binding.entry),
        "availability": {
            "available": availability.available,
            "method": availability.method,
            "executable": availability.executable,
            "path": availability.path,
            "message": availability.message,
        },
    }
