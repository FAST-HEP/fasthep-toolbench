from __future__ import annotations

import datetime as dt
import hashlib
import re
from pathlib import Path

import pytest

from fasthep_toolbench.misc import (
    file_fingerprint,
    file_sha256,
    formatted_today,
    get_file_hash,
)


def test_file_sha256_matches_hashlib(tmp_path: Path) -> None:
    path = tmp_path / "a.bin"
    path.write_bytes(b"abc")

    assert file_sha256(path) == hashlib.sha256(b"abc").hexdigest()
    assert len(file_sha256(path)) == 64


def test_file_sha256_accepts_str_and_path(tmp_path: Path) -> None:
    path = tmp_path / "a.bin"
    path.write_bytes(b"abc")

    assert file_sha256(str(path)) == file_sha256(path)


def test_file_fingerprint_returns_digest_and_size(tmp_path: Path) -> None:
    path = tmp_path / "ten.bin"
    path.write_bytes(b"0123456789")

    digest, size = file_fingerprint(path)

    assert digest == hashlib.sha256(b"0123456789").hexdigest()
    assert size == 10


def test_empty_file_has_the_sha256_of_nothing(tmp_path: Path) -> None:
    path = tmp_path / "empty"
    path.write_bytes(b"")

    assert file_fingerprint(path) == (hashlib.sha256(b"").hexdigest(), 0)


def test_get_file_hash_is_the_first_eight_characters(tmp_path: Path) -> None:
    path = tmp_path / "a.bin"
    path.write_bytes(b"abc")

    assert get_file_hash(path) == file_sha256(path)[:8]


def test_file_sha256_of_a_directory_raises_os_error(tmp_path: Path) -> None:
    with pytest.raises(OSError, match="directory"):
        file_sha256(tmp_path)


def test_file_sha256_of_a_missing_file_raises_file_not_found_error(
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError):
        file_sha256(tmp_path / "missing")


def test_formatted_today_has_the_documented_format() -> None:
    assert re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", formatted_today())


def test_formatted_today_uses_the_given_timezone() -> None:
    tz = dt.timezone(dt.timedelta(hours=14))

    assert formatted_today(tz) == dt.datetime.now(tz=tz).strftime("%Y.%m.%d")
