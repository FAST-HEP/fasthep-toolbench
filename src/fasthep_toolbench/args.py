from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from fasthep_toolbench.model import ToolSpec


def parse_tool_args(spec: ToolSpec, args: Sequence[str]) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    positional: list[str] = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg.startswith("--"):
            key, separator, value = arg[2:].partition("=")
            if not key:
                msg = "Tool option names cannot be empty"
                raise ValueError(msg)
            if not separator:
                if index + 1 < len(args) and not args[index + 1].startswith("--"):
                    index += 1
                    value = args[index]
                else:
                    value = "true"
            parsed[key.replace("-", "_")] = value
        else:
            positional.append(arg)
        index += 1

    ordered_params = list(spec.params)
    for value in positional:
        target = next((name for name in ordered_params if name not in parsed), None)
        if target is None:
            msg = f"Unexpected positional argument '{value}'"
            raise ValueError(msg)
        parsed[target] = value

    for name, param in spec.params.items():
        if name not in parsed and param.has_default:
            parsed[name] = param.default
        if param.required and name not in parsed:
            msg = f"Missing required parameter '{name}'"
            raise ValueError(msg)
    return parsed
