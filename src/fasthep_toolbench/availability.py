from __future__ import annotations

import shutil

from fasthep_toolbench.model import ToolAvailability, ToolSpec


def tool_availability(spec: ToolSpec) -> ToolAvailability:
    executable = spec.availability.get("executable") or spec.executable
    if isinstance(executable, str) and executable:
        path = shutil.which(executable)
        if path is not None:
            return ToolAvailability(
                available=True,
                method="path",
                executable=executable,
                path=path,
            )
        return ToolAvailability(
            available=False,
            method="path",
            executable=executable,
            message=f"{executable} was not found on PATH",
        )
    return ToolAvailability(
        available=False,
        method="unspecified",
        message="No availability check is defined",
    )
