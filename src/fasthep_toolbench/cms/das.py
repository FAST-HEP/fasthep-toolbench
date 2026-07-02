from __future__ import annotations

from typing import Any

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
    },
    "result": {
        "kind": "json",
    },
}


def run_dasgoclient(
    *,
    query: str,
    format: str = "json",
    availability: ToolAvailability | None = None,
) -> dict[str, Any]:
    return {
        "tool": "cms.dasgoclient",
        "status": "placeholder",
        "available": availability.available if availability is not None else None,
        "executable": availability.path if availability is not None else None,
        "query": query,
        "format": format,
        "message": (
            "dasgoclient execution is not implemented yet; "
            "this placeholder establishes the Toolbench extension point."
        ),
    }
