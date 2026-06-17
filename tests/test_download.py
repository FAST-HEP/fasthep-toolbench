from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from fasthep_toolbench.http.download import download_from_url


class FakeResponse:
    def __init__(
        self,
        content: bytes,
        *,
        error: httpx.HTTPStatusError | None = None,
    ) -> None:
        self.content = content
        self.error = error
        self.raise_for_status_called = False

    def raise_for_status(self) -> None:
        self.raise_for_status_called = True
        if self.error is not None:
            raise self.error


def test_download_creates_parent_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_content = b"root bytes"
    response = FakeResponse(expected_content)

    def fake_get(
        url: str,
        *,
        follow_redirects: bool,
        timeout: int,
    ) -> FakeResponse:
        assert url == "https://example.test/data.root"
        assert follow_redirects is True
        assert timeout == 60
        return response

    monkeypatch.setattr("fasthep_toolbench.http.download.httpx.get", fake_get)
    dst = tmp_path / "CMS" / "Zmumu" / "data.root"

    download_from_url("https://example.test/data.root", str(dst))

    assert response.raise_for_status_called
    assert dst.exists()
    assert dst.read_bytes() == expected_content


def test_download_http_failure_propagates_without_creating_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = httpx.Request("GET", "https://example.test/missing.root")
    response = httpx.Response(404, request=request)
    error = httpx.HTTPStatusError(
        "not found",
        request=request,
        response=response,
    )
    fake_response = FakeResponse(b"<html>not found</html>", error=error)

    def fake_get(
        url: str, # noqa: ARG001
        *,
        follow_redirects: bool, # noqa: ARG001
        timeout: int, # noqa: ARG001
    ) -> FakeResponse:
        return fake_response

    monkeypatch.setattr("fasthep_toolbench.http.download.httpx.get", fake_get)
    dst = tmp_path / "CMS" / "Zmumu" / "missing.root"

    with pytest.raises(httpx.HTTPStatusError):
        download_from_url("https://example.test/missing.root", str(dst))

    assert fake_response.raise_for_status_called
    assert not dst.exists()
