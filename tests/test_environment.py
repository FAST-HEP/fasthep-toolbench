from __future__ import annotations

import hashlib
import os
import platform
import shutil
import subprocess
from importlib import metadata
from pathlib import Path
from typing import Any

import pytest

from fasthep_toolbench.command import CommandResult
from fasthep_toolbench.package.environment import (
    distribution_info,
    find_lockfile,
    git_state,
    installed_distributions,
    normalise_name,
    python_info,
)

requires_git = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


class FakeDistribution:
    def __init__(self, name: str, version: str, direct_url: str | None = None) -> None:
        self.metadata = {"Name": name}
        self.version = version
        self._direct_url = direct_url

    def read_text(self, filename: str) -> str | None:
        return self._direct_url if filename == "direct_url.json" else None


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(cwd), "-c", "user.email=t@example.org", "-c", "user.name=t", *args],
        check=True,
        capture_output=True,
    )


def _repository(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q")
    (path / "a.txt").write_text("a", encoding="utf-8")
    _git(path, "add", "a.txt")
    _git(path, "commit", "-q", "-m", "first")
    return path


def test_python_info_has_the_documented_keys() -> None:
    info = python_info()

    assert set(info) == {"version", "implementation", "platform", "executable", "prefix"}
    assert info["version"] == platform.python_version()


def test_normalise_name_collapses_separators_and_case() -> None:
    assert {normalise_name(n) for n in ("Foo_Bar", "foo.bar", "FOO--bar")} == {"foo-bar"}


def test_installed_distributions_lists_pytest_once_sorted() -> None:
    found = installed_distributions()

    assert [name for name, _ in found].count("pytest") == 1
    assert found == sorted(found)


def test_installed_distributions_lists_a_name_found_twice_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fakes = [FakeDistribution("Foo_Bar", "1.0"), FakeDistribution("foo.bar", "2.0")]
    monkeypatch.setattr(metadata, "distributions", lambda: iter(fakes))

    assert installed_distributions() == [("foo-bar", "1.0")]


def test_installed_distributions_skips_distributions_without_a_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    broken = FakeDistribution("x", "0")
    broken.metadata = {}
    monkeypatch.setattr(
        metadata,
        "distributions",
        lambda: iter([broken, FakeDistribution("ok", "1")]),
    )

    assert installed_distributions() == [("ok", "1")]


def test_distribution_info_for_an_installed_package() -> None:
    info = distribution_info("pytest")

    assert info is not None
    assert info.name == "pytest"
    assert info.version == metadata.version("pytest")
    assert info.to_dict()["name"] == "pytest"


def test_distribution_info_for_a_missing_package_is_none() -> None:
    assert distribution_info("definitely-not-installed-xyz") is None


def _patch_distribution(monkeypatch: pytest.MonkeyPatch, dist: FakeDistribution) -> None:
    monkeypatch.setattr(metadata, "distribution", lambda _name: dist)


def test_distribution_info_reads_a_vcs_direct_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    direct = (
        '{"url": "https://github.com/FAST-HEP/fasthep-flow.git",'
        ' "vcs_info": {"vcs": "git", "commit_id": "abc123"}}'
    )
    _patch_distribution(monkeypatch, FakeDistribution("fasthep-flow", "1", direct))

    info = distribution_info("fasthep-flow")

    assert info is not None
    assert info.direct_url is not None
    assert info.direct_url.url == "https://github.com/FAST-HEP/fasthep-flow.git"
    assert info.direct_url.vcs == "git"
    assert info.direct_url.commit_id == "abc123"
    assert info.direct_url.editable is False
    assert info.editable_path is None
    assert info.note is None


def test_distribution_info_reads_an_editable_direct_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    direct = '{"url": "file:///tmp/my%20proj", "dir_info": {"editable": true}}'
    _patch_distribution(monkeypatch, FakeDistribution("proj", "1", direct))

    info = distribution_info("proj")

    assert info is not None
    assert info.direct_url is not None
    assert info.direct_url.editable is True
    assert info.editable_path == "/tmp/my proj"


def test_distribution_info_survives_invalid_direct_url_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_distribution(monkeypatch, FakeDistribution("proj", "1", "{not json"))

    info = distribution_info("proj")

    assert info is not None
    assert info.direct_url is None
    assert info.note is not None
    assert "direct_url.json" in info.note


@requires_git
def test_git_state_of_a_clean_repository(tmp_path: Path) -> None:
    repo = _repository(tmp_path / "repo")
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    state = git_state(repo)

    assert state.revision == head
    assert state.dirty is False
    assert state.root == str(repo.resolve())
    assert state.note is None


@requires_git
def test_git_state_reports_dirty_after_a_tracked_change(tmp_path: Path) -> None:
    repo = _repository(tmp_path / "repo")
    (repo / "a.txt").write_text("changed", encoding="utf-8")

    assert git_state(repo).dirty is True


@requires_git
def test_git_state_ignores_untracked_files(tmp_path: Path) -> None:
    repo = _repository(tmp_path / "repo")
    (repo / "new.txt").write_text("new", encoding="utf-8")

    assert git_state(repo).dirty is False


@requires_git
def test_git_state_in_a_subdirectory_reports_the_repository_root(
    tmp_path: Path,
) -> None:
    repo = _repository(tmp_path / "repo")
    sub = repo / "sub" / "dir"
    sub.mkdir(parents=True)

    state = git_state(sub)

    assert state.root == str(repo.resolve())
    assert state.revision is not None


@requires_git
def test_git_state_outside_a_repository_has_null_values_and_a_note(
    tmp_path: Path,
) -> None:
    state = git_state(tmp_path)

    assert (state.root, state.revision, state.dirty) == (None, None, None)
    assert state.note is not None
    assert "not a git repository" in state.note


def _runner(result: CommandResult) -> Any:
    def run(_command: Any, **_kwargs: Any) -> CommandResult:
        return result

    return run


def test_git_state_without_git_has_a_note_and_does_not_raise(tmp_path: Path) -> None:
    result = CommandResult(["git"], 127, "", "Command not found: git")

    state = git_state(tmp_path, runner=_runner(result))

    assert (state.root, state.revision, state.dirty) == (None, None, None)
    assert state.note is not None
    assert "not found" in state.note


def test_git_state_with_a_refusing_git_keeps_the_first_stderr_line(
    tmp_path: Path,
) -> None:
    result = CommandResult(
        ["git"], 128, "", "fatal: detected dubious ownership in repository\nmore"
    )

    state = git_state(tmp_path, runner=_runner(result))

    assert state.note == "fatal: detected dubious ownership in repository"
    assert state.revision is None


def test_git_state_timeout_is_a_note(tmp_path: Path) -> None:
    result = CommandResult(["git"], 124, "", "", timed_out=True)

    state = git_state(tmp_path, runner=_runner(result))

    assert state.note is not None
    assert "timed out" in state.note


def test_find_lockfile_hashes_the_first_candidate(tmp_path: Path) -> None:
    (tmp_path / "uv.lock").write_bytes(b"lock")

    found = find_lockfile(tmp_path)

    assert found == {
        "name": "uv.lock",
        "sha256": hashlib.sha256(b"lock").hexdigest(),
        "size": 4,
    }


def test_find_lockfile_prefers_pixi_over_uv(tmp_path: Path) -> None:
    (tmp_path / "uv.lock").write_bytes(b"uv")
    (tmp_path / "pixi.lock").write_bytes(b"pixi")

    found = find_lockfile(tmp_path)

    assert found is not None
    assert found["name"] == "pixi.lock"


def test_find_lockfile_without_one_is_none(tmp_path: Path) -> None:
    assert find_lockfile(tmp_path) is None


def test_distribution_info_removes_credentials_from_the_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    direct = (
        '{"url": "https://user:tok3n@github.com/FAST-HEP/fasthep-flow.git",'
        ' "vcs_info": {"vcs": "git", "commit_id": "abc123"}}'
    )
    _patch_distribution(monkeypatch, FakeDistribution("fasthep-flow", "1", direct))

    info = distribution_info("fasthep-flow")

    assert info is not None
    assert info.direct_url is not None
    assert info.direct_url.url == "https://github.com/FAST-HEP/fasthep-flow.git"
    assert "tok3n" not in str(info.to_dict())


def test_distribution_info_keeps_urls_without_credentials_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    direct = '{"url": "https://github.com:443/FAST-HEP/x.git?ref=main"}'
    _patch_distribution(monkeypatch, FakeDistribution("x", "1", direct))

    info = distribution_info("x")

    assert info is not None
    assert info.direct_url is not None
    assert info.direct_url.url == "https://github.com:443/FAST-HEP/x.git?ref=main"


class UnreadableDistribution(FakeDistribution):
    def __init__(self, error: Exception) -> None:
        super().__init__("proj", "1")
        self._error = error

    def read_text(self, _filename: str) -> str | None:
        raise self._error


@pytest.mark.parametrize(
    "error",
    [
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte"),
        PermissionError("denied"),
    ],
)
def test_distribution_info_survives_an_unreadable_direct_url_file(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    _patch_distribution(monkeypatch, UnreadableDistribution(error))

    info = distribution_info("proj")

    assert info is not None
    assert info.direct_url is None
    assert info.note is not None
    assert "direct_url.json" in info.note
    assert "unreadable" in info.note


def test_git_state_disables_repository_controlled_code_and_index_writes(
    tmp_path: Path,
) -> None:
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def run(command: Any, **kwargs: Any) -> CommandResult:
        calls.append((list(command), kwargs))
        return CommandResult(list(command), 0, "abc\n" if "rev-parse" in command else "", "")

    git_state(tmp_path, runner=run)

    assert len(calls) == 3
    for command, kwargs in calls:
        assert command[:2] == ["git", "--no-optional-locks"]
        assert "core.fsmonitor=false" in command
        assert kwargs["env"]["LC_ALL"] == "C"
        assert kwargs["env"].get("PATH") == os.environ.get("PATH")
