from __future__ import annotations

from fasthep_toolbench.command import CommandResult, run_command
from fasthep_toolbench.model import ToolAvailability

D2_SPEC = {
    "name": "d2",
    "kind": "external_tool",
    "version": "1.0",
    "availability": {
        "executable": "d2",
    },
    "install": {
        "method": "github_release",
        "repo": "terrastruct/d2",
        "docs": "https://d2lang.com/tour/install/",
        "releases": "https://github.com/terrastruct/d2/releases",
    },
    "params": {
        "input": {"type": "string", "required": True},
        "output": {"type": "string", "required": False},
        "watch": {"type": "boolean", "default": False},
        "layout": {"type": "string", "required": False},
        "theme": {"type": "string", "required": False},
    },
    "result": {
        "kind": "command",
    },
}


def run_d2(
    *,
    input: str,
    output: str | None = None,
    watch: bool = False,
    layout: str | None = None,
    theme: str | None = None,
    availability: ToolAvailability | None = None,
) -> CommandResult:
    executable = (
        availability.path
        if availability is not None and availability.path is not None
        else "d2"
    )

    command = [executable]

    if watch:
        command.append("-w")

    if layout:
        command.extend(["--layout", layout])

    if theme:
        command.extend(["--theme", theme])

    command.append(input)

    if output:
        command.append(output)

    return run_command(command)
