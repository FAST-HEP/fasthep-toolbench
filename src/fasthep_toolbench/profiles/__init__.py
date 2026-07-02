from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

__all__ = ["registry"]


def registry() -> dict[str, Any]:
    registry_file = resources.files(__package__).joinpath("registry.yaml")
    raw = yaml.safe_load(registry_file.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        msg = "Toolbench profile registry must contain a mapping"
        raise TypeError(msg)
    return raw
