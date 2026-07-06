from __future__ import annotations

import shutil
from pathlib import Path

from fasthep_toolbench.model import ToolAvailability, ToolSpec


def tool_availability(
    spec: ToolSpec,
    *,
    project_dir: Path | None = None,
    global_bin_dir: Path | None = None,
) -> ToolAvailability:
    executable = spec.availability.get("executable") or spec.executable
    if isinstance(executable, str) and executable:
        path = shutil.which(executable)
        if path is not None:
            return ToolAvailability(
                available=True,
                method="path",
                executable=executable,
                path=path,
                source="PATH",
            )
        for source, directory in _candidate_install_dirs(
            project_dir=project_dir,
            global_bin_dir=global_bin_dir,
        ):
            candidate = directory / executable
            if candidate.is_file():
                return ToolAvailability(
                    available=True,
                    method="install_dir",
                    executable=executable,
                    path=str(candidate),
                    source=source,
                )
        return ToolAvailability(
            available=False,
            method="path",
            executable=executable,
            message=f"{executable} was not found on PATH or FAST-HEP install dirs",
        )
    return ToolAvailability(
        available=False,
        method="unspecified",
        message="No availability check is defined",
    )


def _candidate_install_dirs(
    *,
    project_dir: Path | None,
    global_bin_dir: Path | None,
) -> list[tuple[str, Path]]:
    project_root = project_dir or Path.cwd()
    dirs = [("project", project_root / ".fasthep" / "bin")]
    if global_bin_dir is not None:
        dirs.append(("global", global_bin_dir))
    else:
        dirs.append(("global", Path.home() / ".fasthep" / "bin"))
    return dirs
