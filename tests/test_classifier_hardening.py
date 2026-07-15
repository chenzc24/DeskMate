from __future__ import annotations

import csv
from pathlib import Path

import cv2
import numpy as np

from deskmate_baseline.classifier_hardening import build_hardening_datasets
from deskmate_baseline.contracts import INTERNAL_LABELS


CLASS_DIRECTORIES = tuple(
    f"{index}_{label}" for index, label in enumerate(INTERNAL_LABELS)
)


def fixture_source(root: Path) -> None:
    for split, count in (("train", 2), ("val", 1), ("val_cal", 1)):
        for class_index, class_directory in enumerate(CLASS_DIRECTORIES):
            directory = root / split / class_directory
            directory.mkdir(parents=True)
            for image_index in range(count):
                image = np.full(
                    (48 + image_index, 64, 3),
                    (class_index * 30 + image_index * 5) % 255,
                    dtype=np.uint8,
                )
                assert cv2.imwrite(
                    str(directory / f"parent-{class_index}-{image_index}.jpg"), image
                )


def build(source: Path, output: Path):
    return build_hardening_datasets(
        source_root=source,
        output_root=output,
        class_directories=CLASS_DIRECTORIES,
        target_train_images_per_class=4,
        printed_page_labels=("singapura", "pallas"),
        variants=("balanced_oneview", "balanced_print"),
        seed=20260715,
        printed_page={
            "width": 160,
            "height": 120,
            "minimum_jpeg_quality": 60,
            "maximum_jpeg_quality": 80,
        },
    )


def test_build_is_balanced_split_safe_and_deterministic(tmp_path: Path):
    source = tmp_path / "source"
    fixture_source(source)
    rows_a = build(source, tmp_path / "a")
    rows_b = build(source, tmp_path / "b")
    comparable_a = [
        {key: value for key, value in row.items() if key != "output_relative_path"}
        for row in rows_a
    ]
    comparable_b = [
        {key: value for key, value in row.items() if key != "output_relative_path"}
        for row in rows_b
    ]
    assert comparable_a == comparable_b
    for variant in ("balanced_oneview", "balanced_print"):
        for label in INTERNAL_LABELS:
            train = [
                row
                for row in rows_a
                if row["variant"] == variant
                and row["split"] == "train"
                and row["label"] == label
            ]
            assert len(train) == 4
    printed = [row for row in rows_a if row["view_kind"] == "print"]
    assert {row["label"] for row in printed} == {"singapura", "pallas"}
    assert {row["split"] for row in printed} == {"train"}
    assert all(row["variant"] == "balanced_print" for row in printed)
    assert all(
        row["view_kind"] == "base"
        for row in rows_a
        if row["split"] in {"val", "val_cal"}
    )
    with (tmp_path / "a" / "manifest.csv").open(encoding="utf-8-sig") as handle:
        assert len(list(csv.DictReader(handle))) == len(rows_a)
