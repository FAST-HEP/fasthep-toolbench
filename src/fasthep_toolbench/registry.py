from __future__ import annotations

from collections.abc import Mapping
from importlib import metadata, resources
from typing import Any

import yaml

TOOL_REGISTRY_ENTRY_POINT_GROUP = "fasthep_toolbench.registries"


def default_tool_registry_config() -> dict[str, Any]:
    """Load Toolbench's bundled registry layer."""
    registry_file = resources.files("fasthep_toolbench.profiles").joinpath(
        "registry.yaml"
    )
    raw = yaml.safe_load(registry_file.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        msg = "Toolbench registry.yaml must contain a mapping"
        raise TypeError(msg)
    registry = raw.get("registry", raw)
    if not isinstance(registry, dict):
        msg = "Toolbench registry must contain a mapping"
        raise TypeError(msg)
    return registry


def merge_tool_registry_config(
    *configs: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Merge registry layers while keeping raw data at the boundary."""
    merged: dict[str, Any] = {"tools": {}}
    for cfg in configs:
        if not cfg:
            continue
        tools = cfg.get("tools", {})
        if not isinstance(tools, Mapping):
            msg = "Tool registry section 'tools' must be a mapping"
            raise TypeError(msg)
        merged_tools = merged.setdefault("tools", {})
        if not isinstance(merged_tools, dict):
            msg = "Merged tool registry section 'tools' must be a mapping"
            raise TypeError(msg)
        merged_tools.update(dict(tools))
    return merged


def discover_tool_registry_configs() -> list[dict[str, Any]]:
    """Load registry layers published by external packages."""
    configs: list[dict[str, Any]] = []
    for entry_point in metadata.entry_points(group=TOOL_REGISTRY_ENTRY_POINT_GROUP):
        loaded = entry_point.load()
        raw = loaded() if callable(loaded) else loaded
        if not isinstance(raw, dict):
            msg = (
                "Tool registry entry point "
                f"'{entry_point.name}' must return a mapping"
            )
            raise TypeError(msg)
        registry = raw.get("registry", raw)
        if not isinstance(registry, dict):
            msg = (
                "Tool registry entry point "
                f"'{entry_point.name}' must contain a registry mapping"
            )
            raise TypeError(msg)
        configs.append(registry)
    return configs


def resolve_tool_registry_config(
    registry_cfg: Mapping[str, Any] | None = None,
    *,
    include_entry_points: bool = True,
) -> dict[str, Any]:
    discovered = discover_tool_registry_configs() if include_entry_points else []
    return merge_tool_registry_config(
        default_tool_registry_config(),
        *discovered,
        registry_cfg,
    )
