from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from fasthep_toolbench.api import run_registered_tool, tool_info
from fasthep_toolbench.command import CommandResult
from fasthep_toolbench.loader import list_registered_tools


def tools_list_text(
    registry_cfg: Mapping[str, Any] | None = None,
    *,
    include_entry_points: bool = True,
) -> str:
    names = list_registered_tools(
        registry_cfg,
        include_entry_points=include_entry_points,
    )
    if not names:
        return "No tools registered.\n"
    lines = ["Registered tools:"]
    lines.extend(f"  {name}" for name in names)
    return "\n".join(lines) + "\n"


def tool_info_text(
    name: str,
    registry_cfg: Mapping[str, Any] | None = None,
    *,
    include_entry_points: bool = True,
) -> str:
    info = tool_info(
        name,
        registry_cfg,
        include_entry_points=include_entry_points,
    )
    spec = info["spec"]
    availability = info["availability"]
    lines = [
        f"Tool: {name}",
        f"Kind: {spec.kind}",
        f"Version: {spec.version}",
        f"Available: {'yes' if availability['available'] else 'no'}",
    ]
    if availability.get("executable"):
        lines.append(f"Executable: {availability['executable']}")
    if availability.get("path"):
        lines.append(f"Path: {availability['path']}")
    if availability.get("message"):
        lines.append(f"Availability: {availability['message']}")
    method = spec.install.get("method")
    if method:
        lines.append(f"Install method: {method}")
    if spec.params:
        lines.append("Parameters:")
        for param in spec.params.values():
            required = "required" if param.required else "optional"
            suffix = f", default={param.default}" if param.has_default else ""
            lines.append(f"  {param.name}: {param.type} ({required}{suffix})")
    result_kind = spec.result.get("kind")
    if result_kind:
        lines.append(f"Result: {result_kind}")
    return "\n".join(lines) + "\n"


def tool_run_text(
    name: str,
    args: Sequence[str] | None = None,
    registry_cfg: Mapping[str, Any] | None = None,
    *,
    include_entry_points: bool = True,
) -> str:
    result = run_registered_tool(
        name,
        args,
        registry_cfg,
        include_entry_points=include_entry_points,
    )
    if isinstance(result, CommandResult):
        return json.dumps(result.to_dict(tool=name), indent=2, sort_keys=True) + "\n"
    if isinstance(result, str):
        return result if result.endswith("\n") else f"{result}\n"
    return json.dumps(result, indent=2, sort_keys=True) + "\n"
