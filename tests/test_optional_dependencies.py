from __future__ import annotations

import subprocess
import sys

BLOCKER = """
import sys


class _Block:
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in {"rich", "httpx", "tabulate"}:
            raise ImportError(f"blocked {name}")
        return None


sys.meta_path.insert(0, _Block())
"""


def _run(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", BLOCKER + code],
        capture_output=True,
        text=True,
        check=False,
    )


def test_core_package_imports_without_optional_dependencies() -> None:
    result = _run(
        "import fasthep_toolbench\nimport fasthep_toolbench.package.environment\n"
    )

    assert result.returncode == 0, result.stderr


def test_find_fast_hep_packages_works_without_rich() -> None:
    result = _run(
        "from fasthep_toolbench.package import find_fast_hep_packages\n"
        "print(len(find_fast_hep_packages()) >= 0)\n"
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "True"


def test_display_module_names_the_extra_when_rich_is_missing() -> None:
    result = _run("import fasthep_toolbench.display.console\n")

    assert result.returncode != 0
    assert "fasthep-toolbench[display]" in result.stderr


def test_http_module_names_the_extra_when_httpx_is_missing() -> None:
    result = _run("import fasthep_toolbench.http\n")

    assert result.returncode != 0
    assert "fasthep-toolbench[http]" in result.stderr


def test_install_helpers_import_without_httpx_and_fail_only_when_downloading() -> None:
    result = _run(
        "from pathlib import Path\n"
        "import fasthep_toolbench.install as install\n"
        "try:\n"
        "    install.download_d2_release_asset(None, Path('.'), None)\n"
        "except ImportError as exc:\n"
        "    print(exc)\n"
    )

    assert result.returncode == 0, result.stderr
    assert "fasthep-toolbench[http]" in result.stdout
