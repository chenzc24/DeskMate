from __future__ import annotations

from pathlib import Path

from scripts.tools.artifact_inventory import build_inventory


def write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_inventory_reports_registered_and_duplicate_models(tmp_path: Path) -> None:
    write(tmp_path / "models" / "candidate.pt", b"same-weight")
    write(tmp_path / "runs" / "run-1" / "weights" / "best.pt", b"same-weight")
    write(tmp_path / "data" / "downloads" / "dataset-a" / "image.jpg", b"image")
    (tmp_path / "models" / "manifest.yaml").write_text(
        "schema_version: 1\nmodels:\n  - file: models/candidate.pt\n",
        encoding="utf-8",
    )

    report = build_inventory(tmp_path)

    records = {item["path"]: item for item in report["models"]}
    assert records["models/candidate.pt"]["registered"] is True
    assert records["runs/run-1/weights/best.pt"]["registered"] is False
    assert report["duplicate_model_groups"] == [
        ["models/candidate.pt", "runs/run-1/weights/best.pt"]
    ]
    assert report["data_workspaces"][0]["bytes"] == 5


def test_inventory_flags_root_level_model(tmp_path: Path) -> None:
    write(tmp_path / "loose.onnx", b"model")
    (tmp_path / "models").mkdir()
    (tmp_path / "models" / "manifest.yaml").write_text(
        "schema_version: 1\nmodels: []\n", encoding="utf-8"
    )

    report = build_inventory(tmp_path)

    assert report["models"][0]["root_level"] is True
    assert "root_level_model_file" in report["warnings"]
