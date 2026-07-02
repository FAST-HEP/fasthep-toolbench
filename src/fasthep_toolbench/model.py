from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolParam:
    name: str
    type: str = "any"
    required: bool = False
    default: Any = None
    has_default: bool = False

    @classmethod
    def from_obj(cls, name: str, obj: Any) -> ToolParam:
        """Validate and normalise one raw parameter mapping."""
        if not isinstance(obj, Mapping):
            msg = f"Tool parameter '{name}' must be a mapping"
            raise TypeError(msg)
        param_type = obj.get("type", "any")
        if not isinstance(param_type, str) or not param_type:
            msg = f"Tool parameter '{name}' type must be a non-empty string"
            raise TypeError(msg)
        required = obj.get("required", False)
        if not isinstance(required, bool):
            msg = f"Tool parameter '{name}' required must be a boolean"
            raise TypeError(msg)
        return cls(
            name=name,
            type=param_type,
            required=required,
            default=obj.get("default"),
            has_default="default" in obj,
        )

    def to_dict(self) -> dict[str, Any]:
        raw: dict[str, Any] = {"type": self.type}
        if self.required:
            raw["required"] = True
        if self.has_default:
            raw["default"] = self.default
        return raw


@dataclass(frozen=True)
class ToolSpec:
    name: str
    kind: str
    version: str
    params: dict[str, ToolParam]
    install: dict[str, Any]
    result: dict[str, Any]
    availability: dict[str, Any]
    executable: str | None = None

    @classmethod
    def from_obj(cls, obj: Any) -> ToolSpec:
        """Validate a raw external spec once at the registry boundary."""
        if isinstance(obj, ToolSpec):
            return obj
        if not isinstance(obj, Mapping):
            msg = "Tool spec must be a mapping or ToolSpec"
            raise TypeError(msg)

        name = _required_str(obj, "name")
        kind = _optional_str(obj, "kind", "external_tool")
        version = _optional_str(obj, "version", "1.0")
        params = _tool_params(obj.get("params", {}))
        install = _optional_mapping(obj, "install")
        result = _optional_mapping(obj, "result")
        availability = _optional_mapping(obj, "availability")
        executable = obj.get("executable")
        if executable is not None and not isinstance(executable, str):
            msg = "Tool spec executable must be a string"
            raise TypeError(msg)

        return cls(
            name=name,
            kind=kind,
            version=version,
            params=params,
            install=install,
            result=result,
            availability=availability,
            executable=executable,
        )

    def to_dict(self) -> dict[str, Any]:
        raw: dict[str, Any] = {
            "name": self.name,
            "kind": self.kind,
            "version": self.version,
        }
        if self.availability:
            raw["availability"] = dict(self.availability)
        if self.executable is not None:
            raw["executable"] = self.executable
        if self.install:
            raw["install"] = dict(self.install)
        if self.params:
            raw["params"] = {
                name: param.to_dict() for name, param in self.params.items()
            }
        if self.result:
            raw["result"] = dict(self.result)
        return raw


@dataclass(frozen=True)
class ToolAvailability:
    available: bool
    method: str
    executable: str | None = None
    path: str | None = None
    message: str | None = None


@dataclass(frozen=True)
class ToolBinding:
    name: str
    spec: ToolSpec
    impl: Callable[..., Any]
    entry: Mapping[str, Any]


def _required_str(obj: Mapping[str, Any], key: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value:
        msg = f"Tool spec {key} must be a non-empty string"
        raise TypeError(msg)
    return value


def _optional_str(obj: Mapping[str, Any], key: str, default: str) -> str:
    value = obj.get(key, default)
    if not isinstance(value, str) or not value:
        msg = f"Tool spec {key} must be a non-empty string"
        raise TypeError(msg)
    return value


def _optional_mapping(obj: Mapping[str, Any], key: str) -> dict[str, Any]:
    value = obj.get(key, {})
    if not isinstance(value, Mapping):
        msg = f"Tool spec {key} must be a mapping"
        raise TypeError(msg)
    return dict(value)


def _tool_params(obj: Any) -> dict[str, ToolParam]:
    if not isinstance(obj, Mapping):
        msg = "Tool spec params must be a mapping"
        raise TypeError(msg)
    return {
        str(name): ToolParam.from_obj(str(name), raw_param)
        for name, raw_param in obj.items()
    }
