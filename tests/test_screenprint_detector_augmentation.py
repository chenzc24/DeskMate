from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from PIL import Image

from scripts.data import build_screenprint_detector_augmentation as augmentation


FIELDS = [
    "sample_id",
    "breed",
    "split",
    "source_image",
    "source_label",
    "output_image",
    "output_label",
    "width",
    "height",
    "box_count",
    "image_sha256",
    "label_sha256",
]


def test_screenprint_augmentation_accepts_any_positive_breed(
    tmp_path: Path, monkeypatch
) -> None:
    base = tmp_path / "base"
    for sample_id, positive, color in (
        ("ragdoll-1", True, (180, 130, 90)),
        ("negative-1", False, (40, 90, 130)),
    ):
        image = base / "images/train" / f"{sample_id}.jpg"
        label = base / "labels/train" / f"{sample_id}.txt"
        image.parent.mkdir(parents=True, exist_ok=True)
        label.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (160, 120), color).save(image)
        label.write_text("0 0.5 0.5 0.5 0.5\n" if positive else "", encoding="utf-8")
    with (base / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow(
            {
                "sample_id": "ragdoll-1",
                "breed": "ragdoll",
                "split": "train",
                "source_image": "",
                "source_label": "",
                "output_image": "images/train/ragdoll-1.jpg",
                "output_label": "labels/train/ragdoll-1.txt",
                "width": 160,
                "height": 120,
                "box_count": 1,
                "image_sha256": "",
                "label_sha256": "",
            }
        )
        writer.writerow(
            {
                "sample_id": "negative-1",
                "breed": "not_target",
                "split": "train",
                "source_image": "",
                "source_label": "",
                "output_image": "images/train/negative-1.jpg",
                "output_label": "labels/train/negative-1.txt",
                "width": 160,
                "height": 120,
                "box_count": 0,
                "image_sha256": "",
                "label_sha256": "",
            }
        )
    (base / "data.yaml").write_text(
        f"path: {base.as_posix()}\ntrain: images/train\nval: images/val\ntest: images/test\nnames:\n  0: cat\n",
        encoding="utf-8",
    )
    output = tmp_path / "augmented"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_screenprint_detector_augmentation.py",
            "--base-data",
            str(base),
            "--output",
            str(output),
            "--blank-negatives",
            "1",
            "--seed",
            "7",
        ],
    )

    augmentation.main()

    report = json.loads((output / "augmentation_report.json").read_text(encoding="utf-8"))
    assert report["train"] == {
        "original_positive_images": 1,
        "original_background_images": 1,
        "synthetic_screenprint_positive_images": 1,
        "synthetic_blank_panel_negatives": 1,
        "total_images": 4,
    }
    rows = list(csv.DictReader((output / "manifest.csv").open(encoding="utf-8")))
    synthetic = [row for row in rows if row["transform"] == "screenprint_homography"]
    assert len(synthetic) == 1
    assert synthetic[0]["breed"] == "ragdoll"
    generated_label = output / "labels/train" / f"{synthetic[0]['sample_id']}.txt"
    assert generated_label.read_text(encoding="utf-8").startswith("0 ")
    assert (output / "labels/train/synthetic-blank-panel-0001.txt").read_text() == ""
