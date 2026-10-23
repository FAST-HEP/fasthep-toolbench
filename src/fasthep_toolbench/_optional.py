"""Helpers for the optional dependencies (extras) of fasthep-toolbench.

``rich``, ``httpx`` and ``tabulate`` are not required to import the package. Code that needs
them imports them inside the function that uses them (or behind a guarded top-level import in
the modules that are only useful with them) and fails with a message that names the extra.
Plain function-local imports are used because they work on every supported Python version.
"""

from __future__ import annotations

from types import ModuleType
from typing import Any, Self


def missing_extra(feature: str, extra: str) -> ImportError:
    """Return the ``ImportError`` for a feature whose extra is not installed."""
    return ImportError(
        f"{feature} needs the optional dependencies of the {extra!r} extra: "
        f"pip install 'fasthep-toolbench[{extra}]'"
    )


def require_httpx() -> ModuleType:
    """Import and return ``httpx``, or raise an ``ImportError`` that names the extra."""
    try:
        import httpx  # noqa: PLC0415 - optional dependency (extra: http)
    except ImportError as exc:
        feature = "HTTP downloads and tool installation"
        raise missing_extra(feature, "http") from exc
    return httpx


class _PlainConsole:
    """The part of ``rich.console.Console`` used by callers, printing plainly."""

    def print(self, message: str) -> None:
        print(message)  # noqa: T201 - stands in for rich.console.Console.print


class NullProgress:
    """No-op stand-in for ``rich.progress.Progress`` when ``rich`` is not installed."""

    def __init__(self) -> None:
        self.console = _PlainConsole()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def add_task(self, description: str, total: float | None = None) -> int:
        del description, total
        return 0

    def update(self, task_id: int, **kwargs: Any) -> None:
        del task_id, kwargs

    def advance(self, task_id: int, advance: float = 1) -> None:
        del task_id, advance


def spinner_progress() -> Any:
    """Return a transient ``rich`` spinner progress, or a no-op object without ``rich``."""
    try:
        from rich.progress import (  # noqa: PLC0415 - optional dependency (extra: display)
            Progress,
            SpinnerColumn,
            TextColumn,
        )
    except ImportError:
        return NullProgress()
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    )
