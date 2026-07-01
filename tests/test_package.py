from __future__ import annotations

import fasthep_toolbench as m


def test_version():
    assert isinstance(m.__version__, str)
    assert m.__version__
