"""
Copyright (c) 2025 FAST-HEP. All rights reserved.

fasthep-toolbench: Package for cross-package utility functions
"""

from __future__ import annotations

from ._version import version as __version__
from .tools import (
    CommandResult,
    ToolAvailability,
    ToolBinding,
    ToolParam,
    ToolSpec,
    default_tool_registry_config,
    list_registered_tools,
    load_tool_binding,
    load_tool_entry,
    run_command,
    run_registered_tool,
    tool_info,
    tool_info_text,
    tool_run_text,
    tools_list_text,
)

__all__ = [
    "CommandResult",
    "ToolAvailability",
    "ToolBinding",
    "ToolParam",
    "ToolSpec",
    "__version__",
    "default_tool_registry_config",
    "list_registered_tools",
    "load_tool_binding",
    "load_tool_entry",
    "run_command",
    "run_registered_tool",
    "tool_info",
    "tool_info_text",
    "tool_run_text",
    "tools_list_text",
]
