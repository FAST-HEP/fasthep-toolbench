from __future__ import annotations

from typing import Any

from fasthep_toolbench.command import run_command
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
) -> dict[str, Any]:
    executable = (
        availability.path
        if availability is not None and availability.path is not None
        else "dasgoclient"
    )
    result = run_command(
        [
            executable,
            "--query",
            query,
            "--format",
            format,
        ],
        timeout=float(timeout),
    )
    return {
        "tool": "cms.dasgoclient",
        "status": "ok" if result.ok else "error",
        "available": availability.available if availability is not None else None,
        "executable": executable,
        "query": query,
        "format": format,
        "command": result.command,
        "exit_code": result.exit_code,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "timed_out": result.timed_out,
    }
