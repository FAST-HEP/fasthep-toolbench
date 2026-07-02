"""Small Unix-like command executor for external Toolbench integrations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from io import StringIO

import sh


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


def run_command(
    command: Sequence[str],
    *,
    timeout: int | float | None = None,
) -> CommandResult:
    """
    Run an external command on a Unix-like OS.

    The command is always passed as an argument list; no shell parsing or
    shell=True-style behaviour is used.
    """
    if not command:
        msg = "Command must contain at least an executable"
        raise ValueError(msg)

    executable, *args = [str(part) for part in command]
    stdout = StringIO()
    stderr = StringIO()
    try:
        completed = sh.Command(executable)(
            *args,
            _out=stdout,
            _err=stderr,
            _ok_code=list(range(256)),
            _return_cmd=True,
            _timeout=timeout,
        )
    except sh.CommandNotFound:
        return CommandResult(
            command=[executable, *args],
            exit_code=127,
            stdout=stdout.getvalue(),
            stderr=f"Command not found: {executable}",
        )
    except sh.TimeoutException:
        return CommandResult(
            command=[executable, *args],
            exit_code=124,
            stdout=stdout.getvalue(),
            stderr=stderr.getvalue(),
            timed_out=True,
        )

    return CommandResult(
        command=[executable, *args],
        exit_code=int(completed.exit_code),
        stdout=stdout.getvalue(),
        stderr=stderr.getvalue(),
    )
