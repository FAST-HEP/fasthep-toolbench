from __future__ import annotations

from fasthep_toolbench.api import list_registered_tools, run_registered_tool, tool_info
from fasthep_toolbench.args import parse_tool_args
from fasthep_toolbench.availability import tool_availability
from fasthep_toolbench.command import CommandResult, run_command
from fasthep_toolbench.format import tool_info_text, tool_run_text, tools_list_text
from fasthep_toolbench.install import (
    InstallResult,
    default_global_bin_dir,
    install_plan_text,
    install_tool,
    normalize_global_bin_dir,
    project_bin_dir,
)
from fasthep_toolbench.loader import load_object, load_tool_binding, load_tool_entry
from fasthep_toolbench.model import (
    ToolAvailability,
    ToolBinding,
    ToolParam,
    ToolSpec,
)
from fasthep_toolbench.registry import (
    TOOL_REGISTRY_ENTRY_POINT_GROUP,
    default_tool_registry_config,
    discover_tool_registry_configs,
    merge_tool_registry_config,
    resolve_tool_registry_config,
)

__all__ = [
    "TOOL_REGISTRY_ENTRY_POINT_GROUP",
    "CommandResult",
    "InstallResult",
    "ToolAvailability",
    "ToolBinding",
    "ToolParam",
    "ToolSpec",
    "default_global_bin_dir",
    "default_tool_registry_config",
    "discover_tool_registry_configs",
    "install_plan_text",
    "install_tool",
    "list_registered_tools",
    "load_object",
    "load_tool_binding",
    "load_tool_entry",
    "merge_tool_registry_config",
    "normalize_global_bin_dir",
    "parse_tool_args",
    "project_bin_dir",
    "resolve_tool_registry_config",
    "run_command",
    "run_registered_tool",
    "tool_availability",
    "tool_info",
    "tool_info_text",
    "tool_run_text",
    "tools_list_text",
]
