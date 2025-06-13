from __future__ import annotations

import json
from collections.abc import Sequence
from enum import Enum
from itertools import cycle
from typing import Any

from rich.console import Console
from rich.table import Table
from tabulate import tabulate


class DisplayFormats(str, Enum):
    """Display formats for command output"""

    SIMPLE = "simple"
    PIP = "pip"
    TABLE = "table"
    JSON = "json"
    MARKDOWN = "markdown"
    LATEX = "latex"


COLOURS = [
    "cyan",
    "magenta",
    "green",
    "yellow",
    "white",
]


def display(
    data: list[tuple[Any]],
    title: str | None = None,
    headers: list[str] | None = None,
    display_format: DisplayFormats = DisplayFormats.SIMPLE,
) -> None:
    """Display data in console"""
    match display_format:
        case DisplayFormats.SIMPLE | DisplayFormats.PIP:
            separator = "==" if display_format == DisplayFormats.PIP else ": "
            print_simple(data, title, headers, separator=separator)
        case DisplayFormats.TABLE:
            print_table(data, title, headers)
        case DisplayFormats.MARKDOWN:
            print_table_md(data, title, headers)
        case DisplayFormats.LATEX:
            msg = "LaTeX format is not implemented yet."
            raise NotImplementedError(msg)
        case DisplayFormats.JSON:
            console = Console()
            console.print(json.dumps(data, indent=4))
        # case _:
        #     msg = f"Unknown display format: {format}"
        #     raise ValueError(msg)


def print_simple(
    data: list[tuple[Any]],
    title: str | None = None,
    headers: list[str] | None = None,
    separator: str = ":",
) -> None:
    """Print data in simple format"""
    console = Console()
    if title:
        console.rule(
            f"[bold]{title}[/bold]",
            style="cyan",
        )
        # console.print("=" * 10 + f" [bold]{title}[/bold] " + "=" * 10)
    if headers:
        console.print(
            f"{separator}".join(
                f"[{colour}]<{header}>[/]"
                for colour, header in zip(cycle(COLOURS), headers)
            )
        )
    for row in data:
        console.print(
            f"{separator}".join(
                f"[{colour}]{item}[/]" for colour, item in zip(cycle(COLOURS), row)
            )
        )


def print_table(
    data: list[tuple[Any]],
    title: str | None = None,
    headers: list[str] | None = None,
) -> None:
    """Print data in table format"""
    colours = cycle(
        [
            "cyan",
            "magenta",
            "green",
            "yellow",
            "white",
        ]
    )  # Cycle through colors for each row
    # table = packagesList
    if not headers:
        headers = [f"Column {i + 1}" for i in range(len(data[0]))]
    if not title:
        title = "Data Table"
    table = Table(title=title)
    for header in headers:
        table.add_column(header, justify="left", style=next(colours))
    for row in data:
        table.add_row(*[str(item) for item in row])
    console = Console()
    console.print(table)


def print_table_md(
    data: Sequence[Sequence[Any]],
    title: str | None = None,
    headers: Sequence[str] | None = None,
) -> None:
    """Print data in table format"""
    console = Console()
    if title:
        console.rule(
            f"[bold]{title}[/bold]",
            style="cyan",
        )
    if not headers:
        headers = [f"Column {i + 1}" for i in range(len(data[0]))]
    console.print(
        tabulate(
            data,
            headers=headers,
            tablefmt="github",
            colalign=("left", "right"),
        )
    )
