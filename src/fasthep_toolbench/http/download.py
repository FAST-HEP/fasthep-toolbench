"""Functions for download command"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..logger import default_logger

logger = default_logger()


def download_from_url(url: str, destination: str, force: bool = False) -> None:
    """Download a file from a URL"""
    dst = Path(destination)
    if dst.exists() and not force:
        msg = f"File {destination} already exists. Use --force to overwrite. Skipping download."
        logger.warning(msg)
        return
    result = httpx.get(url, follow_redirects=True, timeout=60)
    with dst.open("wb") as file_handle:
        file_handle.write(result.content)


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
        for name, url in data.items():
            progress.update(task, advance=1)
            # TODO: this should be a logger
            output_path = dst / name
            download = progress.add_task(
                f"Downloading {output_path} from {url}", total=None
            )
            download_from_url(url, output_path, force)
            progress.update(download, completed=0)
        progress.update(task, completed=0)
