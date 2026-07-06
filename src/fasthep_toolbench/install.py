"""Project-local external tool installers.

Installers currently assume a Unix-like OS: versioned binaries are exposed
through symlinks such as ``.fasthep/bin/d2 -> d2-<version>``.
"""

from __future__ import annotations

import os
import platform
import tarfile
import zipfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import httpx

from fasthep_toolbench.loader import load_tool_binding
from fasthep_toolbench.model import ToolSpec


@dataclass(frozen=True)
class InstallResult:
    tool: str
    version: str
    binary: Path
    link: Path
    installed: bool
    message: str


def project_bin_dir(project_dir: Path | None = None) -> Path:
    return (project_dir or Path.cwd()) / ".fasthep" / "bin"


def default_global_bin_dir() -> Path:
    return Path.home() / ".fasthep" / "bin"


def normalize_global_bin_dir(path: Path | None = None) -> Path:
    if path is None:
        return default_global_bin_dir()
    expanded = path.expanduser()
    if expanded.name == ".fasthep":
        return expanded / "bin"
    return expanded


def install_tool(
    name: str,
    *,
    install_dir: Path | None = None,
    project_dir: Path | None = None,
    version: str | None = None,
    downloader: Callable[[ToolSpec, Path, str | None], tuple[Path, str]] | None = None,
) -> InstallResult:
    binding = load_tool_binding(name)
    destination = install_dir or project_bin_dir(project_dir)
    destination.mkdir(parents=True, exist_ok=True)

    if name != "d2":
        msg = f"Automatic installation is not implemented for tool '{name}'"
        raise NotImplementedError(msg)

    archive_path, resolved_version = (downloader or download_d2_release_asset)(
        binding.spec,
        destination,
        version,
    )
    binary = _extract_binary(archive_path, destination, "d2", resolved_version)
    link = destination / "d2"
    _replace_symlink(link, binary.name)
    return InstallResult(
        tool=name,
        version=resolved_version,
        binary=binary,
        link=link,
        installed=True,
        message=f"Installed {name} {resolved_version} to {link}",
    )


def install_plan_text(name: str, *, install_dir: Path | None = None) -> str:
    binding = load_tool_binding(name)
    source = _source_text(binding.spec.install)
    link = (install_dir or project_bin_dir()) / str(
        binding.spec.availability.get("executable", binding.spec.name)
    )
    return f"Tool: {name}\nSource: {source}\nInstall path: {link}\n"


def download_d2_release_asset(
    spec: ToolSpec,
    destination: Path,
    version: str | None,
) -> tuple[Path, str]:
    repo = str(spec.install.get("repo", "terrastruct/d2"))
    release = _github_release(repo, version)
    tag = str(release["tag_name"])
    asset = _select_release_asset(release)
    url = str(asset["browser_download_url"])
    filename = str(asset["name"])
    output = destination / filename
    with httpx.stream("GET", url, follow_redirects=True, timeout=60) as response:
        response.raise_for_status()
        with output.open("wb") as stream:
            for chunk in response.iter_bytes():
                stream.write(chunk)
    return output, tag.lstrip("v")


def _github_release(repo: str, version: str | None) -> Mapping[str, Any]:
    suffix = "latest" if version is None else f"tags/{version}"
    url = f"https://api.github.com/repos/{repo}/releases/{suffix}"
    response = httpx.get(url, follow_redirects=True, timeout=60)
    response.raise_for_status()
    raw = response.json()
    if not isinstance(raw, Mapping):
        msg = f"GitHub release response for {repo} must be a mapping"
        raise TypeError(msg)
    return raw


def _select_release_asset(release: Mapping[str, Any]) -> Mapping[str, Any]:
    assets = release.get("assets", [])
    if not isinstance(assets, list):
        msg = "GitHub release assets must be a list"
        raise TypeError(msg)
    system = platform.system().lower()
    machine = platform.machine().lower()
    arch_tokens = ["amd64", "x86_64"] if machine in {"x86_64", "amd64"} else [machine]
    for asset in assets:
        if not isinstance(asset, Mapping):
            continue
        name = str(asset.get("name", "")).lower()
        if (
            system in name
            and any(token in name for token in arch_tokens)
            and name.endswith((".tar.gz", ".tgz", ".zip"))
        ):
            return asset
    msg = f"No compatible d2 release asset found for {system}/{machine}"
    raise ValueError(msg)


def _extract_binary(
    archive_path: Path,
    destination: Path,
    executable: str,
    version: str,
) -> Path:
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path) as archive:
                archive.extractall(tmp_path)
        else:
            with tarfile.open(archive_path) as archive:
                archive.extractall(tmp_path, filter="data")
        source = next(
            path
            for path in tmp_path.rglob(executable)
            if path.is_file() and path.name == executable
        )
        target = destination / f"{executable}-{version}"
        target.write_bytes(source.read_bytes())
        target.chmod(target.stat().st_mode | 0o111)
        return target


def _replace_symlink(link: Path, target_name: str) -> None:
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(target_name)


def _source_text(install: Mapping[str, Any]) -> str:
    repo = install.get("repo")
    method = install.get("method", "unknown")
    if repo:
        return f"GitHub releases, {repo}"
    return str(method)


def prepend_path_env(directory: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["PATH"] = f"{directory}{os.pathsep}{env.get('PATH', '')}"
    return env
