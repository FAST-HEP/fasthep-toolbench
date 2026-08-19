"""Small Unix-like command executor for external Toolbench integrations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
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

    def to_dict(self, *, tool: str | None = None) -> dict[str, object]:
        data: dict[str, object] = {
            "command": self.command,
            "executable": self.command[0] if self.command else None,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "timed_out": self.timed_out,
        }
        if tool is not None:
            data = {"tool": tool, **data}
        return data


def run_command(
    command: Sequence[str],
    *,
    timeout: float | None = None,
    env: Mapping[str, str] | None = None,
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
            _env=dict(env) if env is not None else None,
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
