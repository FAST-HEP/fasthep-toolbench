from __future__ import annotations

from pathlib import Path

from fasthep_toolbench.cms.das import discover_das_datasets, read_dataset_list
from fasthep_toolbench.command import CommandResult


def _groups(tmp_path: Path, text: str) -> list[tuple[str, str | None]]:
    path = tmp_path / "MC.txt"
    path.write_text(text, encoding="utf-8")
    return [
        (entry.dataset, entry.group) for entry in read_dataset_list(path, kind="mc")
    ]


def test_section_headers_set_the_group(tmp_path: Path) -> None:
    text = (
        "##### QCD_Zjet #####\n/Z/A/NANOAODSIM\n\n##### TTbar #####\n/T/A/NANOAODSIM\n"
    )

    assert _groups(tmp_path, text) == [
        ("/Z/A/NANOAODSIM", "QCD_Zjet"),
        ("/T/A/NANOAODSIM", "TTbar"),
    ]


def test_commented_out_datasets_do_not_change_the_group(tmp_path: Path) -> None:
    text = "##### QCD_Zjet #####\n##/Z/old/NANOAODSIM\n#/Z/older/NANOAODSIM\n/Z/A/NANOAODSIM\n"

    assert _groups(tmp_path, text) == [("/Z/A/NANOAODSIM", "QCD_Zjet")]


def test_free_text_comments_do_not_change_the_group(tmp_path: Path) -> None:
    text = (
        "##### QCD_DY #####\n# v2 INVALID in DAS, replaced by:\n/DY/A-v3/NANOAODSIM\n"
    )

    assert _groups(tmp_path, text) == [("/DY/A-v3/NANOAODSIM", "QCD_DY")]


def test_allow_invalid_marker_is_read_and_stripped(tmp_path: Path) -> None:
    path = tmp_path / "MC.txt"
    path.write_text(
        "##### QCD_DY #####\n/DY/Old-v1/NANOAODSIM  # allow-invalid: legacy sample\n/DY/New-v3/NANOAODSIM\n",
        encoding="utf-8",
    )

    entries = read_dataset_list(path, kind="mc")

    assert [(e.dataset, e.allow_invalid) for e in entries] == [
        ("/DY/Old-v1/NANOAODSIM", True),
        ("/DY/New-v3/NANOAODSIM", False),
    ]


def test_discovery_queries_an_allowed_invalid_dataset_with_any_status(
    tmp_path: Path,
) -> None:
    list_dir = tmp_path / "list"
    list_dir.mkdir()
    (list_dir / "DATA.txt").write_text("", encoding="utf-8")
    (list_dir / "MC.txt").write_text(
        "##### QCD_DY #####\n/DY/Old-v1/NANOAODSIM # allow-invalid\n/DY/New-v3/NANOAODSIM\n",
        encoding="utf-8",
    )
    queries: list[str] = []

    def fake_runner(*, query: str, format: str | None, **_: object) -> CommandResult:
        queries.append(query)
        if format is None:
            return CommandResult(
                command=["dasgoclient"],
                exit_code=0,
                stdout="/store/a.root\n",
                stderr="",
            )
        return CommandResult(
            command=["dasgoclient"], exit_code=0, stdout="[]", stderr=""
        )

    discover_das_datasets(
        list_dir=list_dir,
        output_dir=tmp_path / "out",
        era="E",
        version="v",
        runner=fake_runner,
    )

    assert "file dataset=/DY/Old-v1/NANOAODSIM status=*" in queries
    assert "dataset dataset=/DY/Old-v1/NANOAODSIM status=*" in queries
    assert "file dataset=/DY/New-v3/NANOAODSIM" in queries
    assert not any("New-v3" in q and "status=*" in q for q in queries)
