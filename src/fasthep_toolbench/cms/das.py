from __future__ import annotations

from fasthep_toolbench.command import CommandResult, run_command
from fasthep_toolbench.model import ToolAvailability

DASGOCLIENT_SPEC = {
    "name": "cms.dasgoclient",
    "kind": "external_tool",
    "version": "1.0",
    "availability": {
        "executable": "dasgoclient",
    },
    "install": {
        "method": "github_release",
        "repo": "dmwm/dasgoclient",
        "asset": "dasgoclient",
        "target": ".fasthep/bin/dasgoclient",
    },
    "params": {
        "query": {"type": "string", "required": True},
        "format": {"type": "string", "default": "json"},
        "timeout": {"type": "number", "default": 60},
    },
    "result": {
        "kind": "json",
    },
}


def run_dasgoclient(
    *,
    query: str,
    format: str = "json",
    timeout: int | float | str = 60,
    availability: ToolAvailability | None = None,
) -> CommandResult:
    executable = (
        availability.path
        if availability is not None and availability.path is not None
        else "dasgoclient"
    )
    return run_command(
        [
            executable,
            "--query",
            query,
            "--format",
            format,
        ],
        timeout=float(timeout),
    )
