from __future__ import annotations

import importlib.metadata

import fasthep_toolbench as m


def test_version():
    assert importlib.metadata.version("fasthep_toolbench") == m.__version__
