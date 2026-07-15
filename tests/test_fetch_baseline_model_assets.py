from __future__ import annotations

import hashlib
import io
from pathlib import Path

import pytest

from scripts.tools.fetch_baseline_model_assets import ensure_asset


class Response(io.BytesIO):
    def __enter__(self) -> "Response":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


def entry(payload: bytes) -> dict[str, object]:
    return {
        "id": "B-M01-BASE",
        "file": "models/yolo26s-cls.pt",
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "source": {"asset_url": "https://example.invalid/yolo26s-cls.pt"},
    }


def test_ensure_asset_downloads_then_reuses_verified_file(tmp_path: Path) -> None:
    payload = b"pinned model fixture"
    calls = 0

    def opener(_url: str, *, timeout: int) -> Response:
        nonlocal calls
        calls += 1
        assert timeout == 60
        return Response(payload)

    first = ensure_asset(tmp_path, entry(payload), opener=opener)
    second = ensure_asset(tmp_path, entry(payload), opener=opener)
    assert first["state"] == "downloaded_and_verified"
    assert second["state"] == "already_verified"
    assert calls == 1
    assert (tmp_path / "models/yolo26s-cls.pt").read_bytes() == payload


def test_ensure_asset_rejects_bad_download_and_removes_partial(tmp_path: Path) -> None:
    payload = b"expected"

    def opener(_url: str, *, timeout: int) -> Response:
        return Response(b"wrong")

    with pytest.raises(RuntimeError, match="failed checksum"):
        ensure_asset(tmp_path, entry(payload), opener=opener)
    assert not (tmp_path / "models/yolo26s-cls.pt").exists()
    assert not (tmp_path / "models/yolo26s-cls.pt.partial").exists()
