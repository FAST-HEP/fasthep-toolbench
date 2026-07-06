from __future__ import annotations

import shutil
import sys
import tarfile
from pathlib import Path

import pytest

from fasthep_toolbench.cms import das
from fasthep_toolbench.command import CommandResult, run_command
from fasthep_toolbench.graph import d2
from fasthep_toolbench.install import install_plan_text, install_tool
from fasthep_toolbench.model import ToolAvailability
from fasthep_toolbench.tools import (
    ToolSpec,
    default_tool_registry_config,
    list_registered_tools,
    load_tool_binding,
    parse_tool_args,
    run_registered_tool,
    tool_availability,
    tool_info,
    tool_info_text,
    tool_run_text,
    tools_list_text,
)


def test_run_command_captures_success() -> None:
    result = run_command(
        [
            sys.executable,
            "-c",
            "print('hello')",
        ]
    )

    assert result.ok
    assert result.exit_code == 0
    assert result.stdout == "hello\n"
    assert result.stderr == ""


def test_run_command_reports_nonzero_exit() -> None:
    result = run_command(
        [
            sys.executable,
            "-c",
            "import sys; sys.stderr.write('bad'); sys.exit(7)",
        ]
    )

    assert not result.ok
    assert result.exit_code == 7
    assert result.stdout == ""
    assert result.stderr == "bad"


def test_run_command_reports_timeout() -> None:
    result = run_command(
        [
            sys.executable,
            "-c",
            "import time; time.sleep(2)",
        ],
        timeout=0.1,
    )

    assert not result.ok
    assert result.exit_code == 124
    assert result.timed_out


def test_run_command_reports_missing_executable() -> None:
    result = run_command(["definitely-not-a-fasthep-command"])

    assert not result.ok
    assert result.exit_code == 127
    assert result.stderr == "Command not found: definitely-not-a-fasthep-command"


def test_default_registry_contains_builtin_tools() -> None:
    registry = default_tool_registry_config()

    assert registry["tools"]["cms.dasgoclient"] == {
        "spec": "fasthep_toolbench.cms.das:DASGOCLIENT_SPEC",
        "impl": "fasthep_toolbench.cms.das:run_dasgoclient",
    }
    assert registry["tools"]["d2"] == {
        "spec": "fasthep_toolbench.graph.d2:D2_SPEC",
        "impl": "fasthep_toolbench.graph.d2:run_d2",
    }


def test_list_registered_tools_includes_builtin() -> None:
    assert list_registered_tools(include_entry_points=False) == [
        "cms.dasgoclient",
        "d2",
    ]
    assert "cms.dasgoclient" in tools_list_text(include_entry_points=False)
    assert "d2" in tools_list_text(include_entry_points=False)


def test_load_tool_binding_loads_dasgoclient_spec_and_impl() -> None:
    binding = load_tool_binding("cms.dasgoclient", include_entry_points=False)

    assert binding.spec.name == "cms.dasgoclient"
    assert binding.spec.kind == "external_tool"
    assert binding.spec.params["query"].required
    assert binding.impl.__name__ == "run_dasgoclient"


def test_load_tool_binding_loads_d2_spec_and_impl() -> None:
    binding = load_tool_binding("d2", include_entry_points=False)

    assert binding.spec.name == "d2"
    assert binding.spec.kind == "external_tool"
    assert binding.spec.params["input"].required
    assert not binding.spec.params["output"].required
    assert binding.spec.params["format"].default == "svg"
    assert binding.impl.__name__ == "run_d2"


def test_tool_spec_from_obj_normalises_raw_spec() -> None:
    spec = ToolSpec.from_obj(
        {
            "name": "example.tool",
            "kind": "external_tool",
            "params": {
                "query": {"type": "string", "required": True},
                "format": {"type": "string", "default": "json"},
            },
        }
    )

    assert spec.name == "example.tool"
    assert spec.version == "1.0"
    assert spec.params["query"].required
    assert spec.params["format"].default == "json"
    assert spec.to_dict()["params"]["format"] == {
        "type": "string",
        "default": "json",
    }


def test_parse_tool_args_accepts_positional_and_options() -> None:
    spec = ToolSpec.from_obj(
        {
            "name": "example.tool",
            "kind": "external_tool",
            "version": "1.0",
            "params": {
                "query": {"type": "string", "required": True},
                "format": {"type": "string", "default": "json"},
            },
        }
    )

    assert parse_tool_args(spec, ["/Dataset/Run/TIER", "--format", "plain"]) == {
        "query": "/Dataset/Run/TIER",
        "format": "plain",
    }


def test_parse_tool_args_requires_required_params() -> None:
    spec = ToolSpec.from_obj(
        {
            "name": "example.tool",
            "kind": "external_tool",
            "params": {
                "query": {"type": "string", "required": True},
            },
        }
    )

    with pytest.raises(ValueError, match="Missing required parameter 'query'"):
        parse_tool_args(spec, [])


def test_tool_info_reports_metadata() -> None:
    info = tool_info("cms.dasgoclient", include_entry_points=False)

    assert info["spec"].install["method"] == "github_release"
    assert info["availability"]["executable"] == "dasgoclient"
    text = tool_info_text("cms.dasgoclient", include_entry_points=False)
    assert "Tool: cms.dasgoclient" in text
    assert "Install method: github_release" in text


def test_d2_tool_info_reports_metadata() -> None:
    info = tool_info("d2", include_entry_points=False)

    assert info["spec"].install["method"] == "github_release"
    assert info["spec"].install["repo"] == "terrastruct/d2"
    assert info["spec"].install["docs"] == "https://d2lang.com/tour/install/"
    assert info["availability"]["executable"] == "d2"
    text = tool_info_text("d2", include_entry_points=False)
    assert "Tool: d2" in text
    assert "Install method: github_release" in text


def test_tool_availability_finds_project_local_binary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(shutil, "which", lambda _: None)
    binary = tmp_path / ".fasthep" / "bin" / "d2"
    binary.parent.mkdir(parents=True)
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o755)
    binding = load_tool_binding("d2", include_entry_points=False)

    availability = tool_availability(binding.spec, project_dir=tmp_path)

    assert availability.available
    assert availability.method == "install_dir"
    assert availability.source == "project"
    assert availability.path == str(binary)


def test_install_tool_writes_versioned_binary_and_link(tmp_path: Path) -> None:
    archive = tmp_path / "d2.tar.gz"
    source = tmp_path / "source" / "d2"
    source.parent.mkdir()
    source.write_text("#!/bin/sh\n", encoding="utf-8")
    source.chmod(0o755)
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(source, arcname="d2")

    def fake_downloader(spec: ToolSpec, destination: Path, version: str | None) -> tuple[Path, str]:
        assert spec.name == "d2"
        assert destination == tmp_path / ".fasthep" / "bin"
        assert version is None
        return archive, "0.7.0"

    result = install_tool("d2", project_dir=tmp_path, downloader=fake_downloader)

    assert result.binary == tmp_path / ".fasthep" / "bin" / "d2-0.7.0"
    assert result.binary.exists()
    assert result.binary.stat().st_mode & 0o111
    assert result.link == tmp_path / ".fasthep" / "bin" / "d2"
    assert result.link.is_symlink()
    assert result.link.readlink() == Path("d2-0.7.0")
    assert result.message == f"Installed d2 0.7.0 to {result.link}"


def test_install_plan_text_reports_d2_source_and_path(tmp_path: Path) -> None:
    text = install_plan_text("d2", install_dir=tmp_path / ".fasthep" / "bin")

    assert "Tool: d2" in text
    assert "Source: GitHub releases, terrastruct/d2" in text
    assert f"Install path: {tmp_path / '.fasthep' / 'bin' / 'd2'}" in text


def test_run_registered_tool_uses_dasgoclient_executor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run_command(
        command: list[str],
        *,
        timeout: int | float | None = None,  # noqa: ARG001
    ) -> CommandResult:
        return CommandResult(
            command=command,
            exit_code=0,
            stdout='[{"dataset": "example"}]\n',
            stderr="",
        )

    monkeypatch.setattr(das, "run_command", fake_run_command)

    result = run_registered_tool(
        "cms.dasgoclient",
        ["/Dataset/Run/TIER"],
        include_entry_points=False,
    )

    assert isinstance(result, CommandResult)
    assert result.exit_code == 0
    assert result.stdout == '[{"dataset": "example"}]\n'
    assert result.command[-4:] == [
        "--query",
        "/Dataset/Run/TIER",
        "--format",
        "json",
    ]


def test_tool_run_text_formats_structured_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run_command(
        command: list[str],
        *,
        timeout: int | float | None = None,  # noqa: ARG001
    ) -> CommandResult:
        return CommandResult(command=command, exit_code=0, stdout="[]\n", stderr="")

    monkeypatch.setattr(das, "run_command", fake_run_command)

    text = tool_run_text(
        "cms.dasgoclient",
        ["/Dataset/Run/TIER"],
        include_entry_points=False,
    )

    assert '"tool": "cms.dasgoclient"' in text
    assert '"exit_code":' in text


def test_registry_cfg_can_add_external_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = {
        "tools": {
            "example.dasgoclient": {
                "spec": "fasthep_toolbench.cms.das:DASGOCLIENT_SPEC",
                "impl": "fasthep_toolbench.cms.das:run_dasgoclient",
            }
        }
    }

    assert "example.dasgoclient" in list_registered_tools(
        registry,
        include_entry_points=False,
    )
    monkeypatch.setattr(
        das,
        "run_command",
        lambda command, *, timeout=None: CommandResult(  # noqa: ARG005
            command=command,
            exit_code=0,
            stdout="",
            stderr="",
        ),
    )
    result = run_registered_tool(
        "example.dasgoclient",
        ["hello"],
        registry,
        include_entry_points=False,
    )
    assert isinstance(result, CommandResult)
    assert result.command[-4:] == ["--query", "hello", "--format", "json"]


def test_dasgoclient_runs_through_command_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[list[str], int | float | None]] = []

    def fake_run_command(
        command: list[str],
        *,
        timeout: int | float | None = None,
    ) -> CommandResult:
        calls.append((command, timeout))
        return CommandResult(
            command=command,
            exit_code=2,
            stdout="",
            stderr="das error",
        )

    monkeypatch.setattr(das, "run_command", fake_run_command)

    result = das.run_dasgoclient(
        query="/Dataset/Run/TIER",
        format="json",
        timeout=5,
        availability=ToolAvailability(
            available=True,
            method="path",
            executable="dasgoclient",
            path="/tmp/dasgoclient",
        ),
    )

    assert calls == [
        (
            ["/tmp/dasgoclient", "--query", "/Dataset/Run/TIER", "--format", "json"],
            5.0,
        )
    ]
    assert result.exit_code == 2
    assert result.stderr == "das error"


def test_d2_runs_through_command_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_run_command(command: list[str]) -> CommandResult:
        calls.append(command)
        return CommandResult(command=command, exit_code=0, stdout="", stderr="")

    monkeypatch.setattr(d2, "run_command", fake_run_command)

    result = d2.run_d2(
        input="input.d2",
        output="output.svg",
        format="svg",
        layout="elk",
        theme="300",
        availability=ToolAvailability(
            available=True,
            method="path",
            executable="d2",
            path="/tmp/d2",
        ),
    )

    assert calls == [
        [
            "/tmp/d2",
            "input.d2",
            "output.svg",
            "--format",
            "svg",
            "--layout",
            "elk",
            "--theme",
            "300",
        ]
    ]
    assert result.ok


def test_registered_d2_accepts_positional_input_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_run_command(command: list[str]) -> CommandResult:
        calls.append(command)
        return CommandResult(command=command, exit_code=0, stdout="rendered", stderr="")

    monkeypatch.setattr(d2, "run_command", fake_run_command)

    result = run_registered_tool(
        "d2",
        ["input.d2", "output.svg"],
        include_entry_points=False,
    )

    assert isinstance(result, CommandResult)
    assert calls == [["d2", "input.d2", "output.svg", "--format", "svg"]]
    assert result.stdout == "rendered"


def test_d2_tool_run_text_formats_structured_command_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        d2,
        "run_command",
        lambda command: CommandResult(  # noqa: ARG005
            command=["d2", "input.d2", "output.svg"],
            exit_code=0,
            stdout="",
            stderr="",
        ),
    )

    text = tool_run_text(
        "d2",
        ["input.d2", "output.svg"],
        include_entry_points=False,
    )

    assert '"tool": "d2"' in text
    assert '"command": [' in text
