"""Pure inspection of the Python environment and of git checkouts.

Everything here is quiet and import-safe: no progress output, no network, no subprocess at
import time. The environment is described from the running interpreter with
``importlib.metadata`` and, for git state, with the ``git`` executable; nothing depends on a
lock file, ``pixi`` or ``conda`` (a plain ``pip install`` environment must work).
"""

from __future__ import annotations

import json
import os
import platform
import re
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass
from importlib import metadata
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlsplit, urlunsplit
from urllib.request import url2pathname

from fasthep_toolbench.command import CommandResult, run_command
from fasthep_toolbench.misc import file_fingerprint

LOCKFILE_CANDIDATES = ("pixi.lock", "uv.lock", "poetry.lock", "Pipfile.lock")


@dataclass(frozen=True)
class DirectUrl:
    """The parsed ``direct_url.json`` of an installed distribution."""

    url: str
    vcs: str | None
    commit_id: str | None
    editable: bool


@dataclass(frozen=True)
class DistributionInfo:
    name: str
    version: str
    editable_path: str | None
    direct_url: DirectUrl | None
    note: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GitState:
    """Revision and dirty flag of a git checkout; ``None`` values come with a ``note``."""

    root: str | None
    revision: str | None
    dirty: bool | None
    note: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def python_info() -> dict[str, str]:
    """Describe the running interpreter."""
    return {
        "version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "executable": sys.executable,
        "prefix": sys.prefix,
    }


def normalise_name(name: str) -> str:
    """Normalise a distribution name as in PEP 503 (lower case, runs of ``-_.`` become ``-``)."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _distribution_name(dist: Any) -> str | None:
    try:
        raw = dist.metadata["Name"]
    except KeyError:
        return None
    return normalise_name(raw) if raw else None


def installed_distributions() -> list[tuple[str, str]]:
    """Return ``(normalised name, version)`` of every installed distribution, sorted.

    A distribution that is found more than once on ``sys.path`` is listed once (the first
    one wins, as in import resolution).
    """
    found: dict[str, str] = {}
    for dist in metadata.distributions():
        name = _distribution_name(dist)
        if name is not None and name not in found:
            found[name] = dist.version
    return sorted(found.items())


def distribution_info(name: str) -> DistributionInfo | None:
    """Describe one installed distribution, or return ``None`` when it is not installed."""
    try:
        dist = metadata.distribution(name)
    except metadata.PackageNotFoundError:
        return None
    direct_url, editable_path, note = _read_direct_url(dist)
    return DistributionInfo(
        name=_distribution_name(dist) or normalise_name(name),
        version=dist.version,
        editable_path=editable_path,
        direct_url=direct_url,
        note=note,
    )


def _read_direct_url(dist: Any) -> tuple[DirectUrl | None, str | None, str | None]:
    try:
        text = dist.read_text("direct_url.json")
    except (OSError, UnicodeDecodeError) as exc:
        return None, None, f"direct_url.json is unreadable ({type(exc).__name__})"
    if text is None:
        return None, None, None
    try:
        data = json.loads(text)
    except ValueError:
        return None, None, "direct_url.json is not valid JSON"
    if not isinstance(data, dict) or not isinstance(data.get("url"), str):
        return None, None, "direct_url.json has no url"
    raw_vcs = data.get("vcs_info")
    vcs_info: dict[str, Any] = raw_vcs if isinstance(raw_vcs, dict) else {}
    raw_dir = data.get("dir_info")
    dir_info: dict[str, Any] = raw_dir if isinstance(raw_dir, dict) else {}
    editable = bool(dir_info.get("editable"))
    url = data["url"]
    direct = DirectUrl(
        url=_redact_url(url),
        vcs=vcs_info.get("vcs"),
        commit_id=vcs_info.get("commit_id"),
        editable=editable,
    )
    editable_path = None
    if editable:
        parsed = urlparse(url)
        if parsed.scheme == "file":
            editable_path = url2pathname(parsed.path)
    return direct, editable_path, None


def _redact_url(url: str) -> str:
    """Remove ``user:password@`` from a URL: the result is recorded in manifests."""
    parts = urlsplit(url)
    if "@" not in parts.netloc:
        return url
    return urlunsplit(parts._replace(netloc=parts.netloc.rsplit("@", 1)[1]))


def git_state(
    path: Path | str,
    *,
    timeout: float = 5.0,
    runner: Callable[..., CommandResult] = run_command,
) -> GitState:
    """Return the repository root, revision and dirty flag for ``path``; never raises.

    ``dirty`` means tracked files differ from ``HEAD`` (untracked files are ignored). When
    ``git`` is missing, times out, refuses to run (for example "dubious ownership") or the
    path is not in a repository, the affected values are ``None`` and ``note`` says why.

    Every call runs with ``core.fsmonitor`` disabled (a repository can configure a program to
    be run by ``git status``) and ``--no-optional-locks`` (no index writes on read-only or
    shared trees), and with ``LC_ALL=C`` so that the notes do not depend on the locale.
    """
    target = str(path)
    env = {**os.environ, "LC_ALL": "C"}

    def git(*args: str) -> CommandResult:
        command = [
            "git",
            "--no-optional-locks",
            "-C",
            target,
            "-c",
            "core.fsmonitor=false",
            *args,
        ]
        return runner(command, timeout=timeout, env=env)

    top = git("rev-parse", "--show-toplevel")
    if not top.ok:
        return GitState(None, None, None, _failure_note(top, target, timeout))
    root = top.stdout.strip()
    head = git("rev-parse", "HEAD")
    if not head.ok:
        return GitState(root, None, None, _failure_note(head, target, timeout))
    revision = head.stdout.strip()
    status = git("status", "--porcelain", "--untracked-files=no")
    if not status.ok:
        return GitState(root, revision, None, _failure_note(status, target, timeout))
    return GitState(root, revision, bool(status.stdout.strip()), None)


def _failure_note(result: CommandResult, target: str, timeout: float) -> str:
    if result.timed_out:
        return f"git timed out after {timeout}s"
    if result.exit_code == 127:
        return "git not found"
    stderr = result.stderr.strip()
    if "not a git repository" in stderr.lower():
        return f"not a git repository: {target}"
    first_line = stderr.splitlines()[0].strip() if stderr else ""
    return first_line or f"git exited with {result.exit_code}"


def find_lockfile(root: Path | str) -> dict[str, Any] | None:
    """Describe the first lock file found in ``root``, or ``None``.

    Opportunistic only: nothing may depend on a lock file being present.
    """
    for name in LOCKFILE_CANDIDATES:
        candidate = Path(root) / name
        if not candidate.is_file():
            continue
        try:
            digest, size = file_fingerprint(candidate)
        except OSError as exc:
            return {"name": name, "sha256": None, "size": None, "note": str(exc)}
        return {"name": name, "sha256": digest, "size": size}
    return None
