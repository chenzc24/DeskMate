"""Rebuild the five-breed classifier source dataset after manual review.

The review package is deletion-driven. Remaining files are accepted, and a
file moved between class directories is treated as a corrected class label.
Validation and calibration splits are preserved from the frozen M8 source.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LABELS = ("ragdoll", "singapura", "persian", "sphynx", "pallas")
CLASS_DIRS = {label: f"{index}_{label}" for index, label in enumerate(LABELS)}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def materialize(source: Path, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
        return "hardlink"
    except OSError:
        shutil.copy2(source, destination)
        return "copy"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--review-root",
        type=Path,
        default=ROOT / "data/downloads/manual_source_review_20260715",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / "data/downloads/baseline_target5_machine_merged_20260715",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/downloads/baseline_target5_manual_curated_20260715",
    )
    args = parser.parse_args()

    review_root = args.review_root.resolve()
    source = args.source.resolve()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(output)

    source_dataset = source / "one_view_yolo_classify"
    output_dataset = output / "one_view_yolo_classify"
    with (source / "target5_manifest.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        source_rows = list(csv.DictReader(handle))
        fields = list(source_rows[0])

    original_train_by_name: dict[str, dict[str, str]] = {}
    for row in source_rows:
        if row["split"] != "train":
            continue
        name = Path(row["dataset_relative_path"]).name
        if name in original_train_by_name:
            raise ValueError(f"duplicate source train filename: {name}")
        original_train_by_name[name] = row

    reviewed: dict[str, tuple[str, Path]] = {}
    for label, class_dir in CLASS_DIRS.items():
        directory = review_root / "01_classifier_m8_original" / class_dir
        for path in sorted(directory.iterdir()):
            if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            if path.name in reviewed:
                raise ValueError(f"duplicate reviewed filename: {path.name}")
            if path.name not in original_train_by_name:
                raise ValueError(f"reviewed file not present in frozen source: {path}")
            source_row = original_train_by_name[path.name]
            if sha256_file(path) != source_row["view_sha256"]:
                raise ValueError(f"reviewed file content changed: {path}")
            reviewed[path.name] = (label, path)

    output_rows: list[dict[str, str]] = []
    materialization: Counter[str] = Counter()
    deleted_by_label: Counter[str] = Counter()
    relabelled: list[dict[str, str]] = []

    for row in source_rows:
        split = row["split"]
        original_relative = Path(row["dataset_relative_path"])
        if split == "train":
            name = original_relative.name
            if name not in reviewed:
                deleted_by_label[row["label"]] += 1
                continue
            label, source_path = reviewed[name]
            relative = Path("train") / CLASS_DIRS[label] / name
            if label != row["label"]:
                relabelled.append(
                    {
                        "sample_id": row["sample_id"],
                        "from": row["label"],
                        "to": label,
                        "filename": name,
                    }
                )
            updated = dict(row)
            updated["label"] = label
            updated["source_kind"] = "manual_source_review_accepted"
            updated["source_path"] = str(source_path)
            updated["source_sha256"] = sha256_file(source_path)
            updated["dataset_relative_path"] = relative.as_posix()
            updated["view_sha256"] = updated["source_sha256"]
            updated["route_mode"] = "manual_review_survivor"
            updated["route_reason"] = "accepted_or_relabelled_in_manual_source_review"
        else:
            source_path = source_dataset / original_relative
            relative = original_relative
            updated = dict(row)
        destination = output_dataset / relative
        materialization[materialize(source_path, destination)] += 1
        output_rows.append(updated)

    output.mkdir(parents=True, exist_ok=True)
    manifest = output / "target5_manifest.csv"
    with manifest.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)

    counts = Counter((row["split"], row["label"]) for row in output_rows)
    final_counts = {
        split: {label: counts[(split, label)] for label in LABELS}
        for split in ("train", "val", "val_cal")
    }
    report = {
        "schema_version": 1,
        "status": "TARGET5_DATASET_READY",
        "source_root": str(source),
        "review_root": str(review_root),
        "dataset_root": str(output_dataset),
        "manifest": str(manifest),
        "manifest_sha256": sha256_file(manifest),
        "labels": list(LABELS),
        "not_target_present": False,
        "final_counts": final_counts,
        "total": len(output_rows),
        "manual_review": {
            "original_train_images": len(original_train_by_name),
            "accepted_train_images": len(reviewed),
            "deleted_train_images": len(original_train_by_name) - len(reviewed),
            "deleted_by_original_label": dict(deleted_by_label),
            "relabelled": relabelled,
        },
        "materialization": dict(materialization),
        "validation_policy": "frozen M8 val and val_cal preserved unchanged",
        "robot_diagnostic_images_in_training": 0,
    }
    (output / "target5_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
