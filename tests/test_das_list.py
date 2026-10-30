from __future__ import annotations

from pathlib import Path

from fasthep_toolbench.cms.das import read_dataset_list


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
