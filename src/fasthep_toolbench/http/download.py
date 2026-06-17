"""Functions for download command"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import httpx
from rich.progress import Progress, SpinnerColumn, TextColumn

DownloadStatus = Literal["downloaded", "skipped"]


def download_from_url(
    url: str, destination: str, force: bool = False
) -> DownloadStatus:
    """Download a file from a URL"""
    dst = Path(destination)
    if dst.exists() and not force:
        return "skipped"

    result = httpx.get(url, follow_redirects=True, timeout=60)
    result.raise_for_status()

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(result.content)

    return "downloaded"


def download_from_json(json_input: str, destination: str, force: bool = False) -> None:
    """Download files specified in JSON input file into destination directory.
    JSON input file should be a dictionary with the following structure:
    {   "file1": "url1", "file2": "url2", ... }
    """
    dst = Path(destination)
    with Path(json_input).open(encoding="utf-8") as json_file:
        data = json.load(json_file)
    if not dst.exists():
        dst.mkdir(parents=True, exist_ok=True)
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Downloading files...", total=len(data))
        downloaded = 0
        skipped = 0

        for name, url in data.items():
            output_path = dst / name

            progress.update(task, description=f"Checking {output_path}")
            status = download_from_url(url, output_path, force)

            if status == "downloaded":
                downloaded += 1
            else:
                skipped += 1

            progress.advance(task)
        progress.console.print(
            f"Downloaded {downloaded} file(s), skipped {skipped} existing file(s)."
        )
