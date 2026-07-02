from __future__ import annotations

import pytest

from fasthep_toolbench.tools import (
    ToolSpec,
    default_tool_registry_config,
    list_registered_tools,
    load_tool_binding,
    parse_tool_args,
    run_registered_tool,
    tool_info,
    tool_info_text,
    tool_run_text,
    tools_list_text,
)


def test_default_registry_contains_dasgoclient() -> None:
    registry = default_tool_registry_config()

    assert registry["tools"]["cms.dasgoclient"] == {
        "spec": "fasthep_toolbench.cms.das:DASGOCLIENT_SPEC",
        "impl": "fasthep_toolbench.cms.das:run_dasgoclient",
    }


def test_list_registered_tools_includes_builtin() -> None:
    assert list_registered_tools(include_entry_points=False) == ["cms.dasgoclient"]
    assert "cms.dasgoclient" in tools_list_text(include_entry_points=False)


def test_load_tool_binding_loads_spec_and_impl() -> None:
    binding = load_tool_binding("cms.dasgoclient", include_entry_points=False)

    assert binding.spec.name == "cms.dasgoclient"
    assert binding.spec.kind == "external_tool"
    assert binding.spec.params["query"].required
    assert binding.impl.__name__ == "run_dasgoclient"


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


def test_run_registered_tool_returns_placeholder() -> None:
    result = run_registered_tool(
        "cms.dasgoclient",
        ["/Dataset/Run/TIER"],
        include_entry_points=False,
    )

    assert result["tool"] == "cms.dasgoclient"
    assert result["status"] == "placeholder"
    assert result["query"] == "/Dataset/Run/TIER"
    assert result["format"] == "json"


def test_tool_run_text_formats_structured_result() -> None:
    text = tool_run_text(
        "cms.dasgoclient",
        ["/Dataset/Run/TIER"],
        include_entry_points=False,
    )

    assert '"tool": "cms.dasgoclient"' in text
    assert '"status": "placeholder"' in text


def test_registry_cfg_can_add_external_tool() -> None:
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
    result = run_registered_tool(
        "example.dasgoclient",
        ["hello"],
        registry,
        include_entry_points=False,
    )
    assert result["tool"] == "cms.dasgoclient"
    assert result["query"] == "hello"
