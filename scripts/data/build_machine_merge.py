from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import time
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from deskmate_baseline.domain.contracts import FramePacket
from deskmate_baseline.perception.localization import (
    UltralyticsCatLocalizerBackend,
    route_classification_roi,
)


ROOT = Path(__file__).resolve().parents[2]
LABELS = ("ragdoll", "singapura", "persian", "sphynx", "pallas", "not_target")
CLASS_DIRS = {label: f"{index}_{label}" for index, label in enumerate(LABELS)}
MACHINE_FOLDER_LABELS = {
    "ragdoll": "ragdoll",
    "singapura cat": "singapura",
    "persian": "persian",
    "sphynx": "sphynx",
    "pallas": "pallas",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def link_or_copy(source: Path, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
        return "hardlink"
    except OSError:
        shutil.copy2(source, destination)
        return "copy"


def read_image(path: Path) -> np.ndarray:
    image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"cannot decode image: {path}")
    return image


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base",
        type=Path,
        default=ROOT / "data/downloads/baseline_merged_gapfill_nocat_20260715",
    )
    parser.add_argument(
        "--machine-source",
        type=Path,
        default=Path(r"C:\Users\90590\Desktop\pic\pic"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/downloads/baseline_nocat_machine_merged_20260715",
    )
    args = parser.parse_args()
    base = args.base.resolve()
    machine_source = args.machine_source.resolve()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    base_dataset = base / "one_view_yolo_classify"
    dataset = output / "one_view_yolo_classify"
    rows: list[dict[str, object]] = []
    materialization: Counter[str] = Counter()
    existing_hashes: set[str] = set()
    for split in ("train", "val", "val_cal"):
        for label in LABELS:
            source_directory = base_dataset / split / CLASS_DIRS[label]
            if not source_directory.is_dir():
                raise FileNotFoundError(source_directory)
            for source in sorted(path for path in source_directory.iterdir() if path.is_file()):
                destination = dataset / split / CLASS_DIRS[label] / source.name
                method = link_or_copy(source, destination)
                materialization[method] += 1
                digest = sha256_file(source)
                existing_hashes.add(digest)
                rows.append(
                    {
                        "sample_id": f"base-{split}-{label}-{source.stem}",
                        "label": label,
                        "split": split,
                        "source_kind": "baseline_merged_gapfill_nocat",
                        "source_path": str(source),
                        "source_sha256": digest,
                        "dataset_relative_path": destination.relative_to(dataset).as_posix(),
                        "view_sha256": digest,
                        "route_mode": "frozen_base_view",
                        "route_reason": "preserved_from_base_dataset",
                        "detector_box_count": "",
                    }
                )
    detector_path = ROOT / "models/yolo26s.pt"
    detector = UltralyticsCatLocalizerBackend(
        checkpoint=detector_path,
        device=0,
        imgsz=640,
        confidence_threshold=0.25,
        minimum_box_area_ratio=0.02,
        maximum_frame_age_ms=5000,
    )
    detector.load()
    detector.warmup()
    machine_source_hashes: set[str] = set()
    skipped_exact_source_duplicates = 0
    skipped_existing_view_duplicates = 0
    frame_id = 0
    for folder in sorted(path for path in machine_source.iterdir() if path.is_dir()):
        normalized = folder.name.strip().casefold()
        if normalized not in MACHINE_FOLDER_LABELS:
            raise ValueError(f"unknown machine-view label folder: {folder.name}")
        label = MACHINE_FOLDER_LABELS[normalized]
        ordinal = 0
        for source in sorted(
            path
            for path in folder.iterdir()
            if path.is_file() and path.suffix.casefold() in {".jpg", ".jpeg", ".png"}
        ):
            source_digest = sha256_file(source)
            if source_digest in machine_source_hashes:
                skipped_exact_source_duplicates += 1
                continue
            machine_source_hashes.add(source_digest)
            image = read_image(source)
            height, width = image.shape[:2]
            frame = FramePacket(
                frame_id=frame_id,
                captured_at_ns=time.time_ns(),
                image_bgr=image,
                source=str(source),
                width=width,
                height=height,
            )
            observation = detector.infer(frame)
            routed = route_classification_roi(
                frame,
                observation,
                box_is_stable=bool(observation.valid and observation.boxes),
                padding_ratio=0.15,
                fallback_center_scale=0.8,
                minimum_padded_short_side_pixels=32,
            )
            success, encoded = cv2.imencode(
                ".jpg", routed.image_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95]
            )
            if not success:
                raise RuntimeError(f"cannot encode routed ROI: {source}")
            view_digest = hashlib.sha256(encoded.tobytes()).hexdigest()
            if view_digest in existing_hashes:
                skipped_existing_view_duplicates += 1
                continue
            existing_hashes.add(view_digest)
            ordinal += 1
            destination = (
                dataset
                / "train"
                / CLASS_DIRS[label]
                / f"machine-{label}-{ordinal:03d}.jpg"
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            encoded.tofile(str(destination))
            if sha256_file(destination) != view_digest:
                raise RuntimeError(f"written view hash mismatch: {destination}")
            rows.append(
                {
                    "sample_id": f"machine-{label}-{ordinal:03d}",
                    "label": label,
                    "split": "train",
                    "source_kind": "machine_camera_view",
                    "source_path": str(source),
                    "source_sha256": source_digest,
                    "dataset_relative_path": destination.relative_to(dataset).as_posix(),
                    "view_sha256": view_digest,
                    "route_mode": routed.mode,
                    "route_reason": routed.route_reason,
                    "detector_box_count": len(observation.boxes),
                }
            )
            frame_id += 1
    output.mkdir(parents=True, exist_ok=True)
    manifest = output / "merged_manifest.csv"
    with manifest.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    counts = Counter((str(row["split"]), str(row["label"])) for row in rows)
    final_counts = {
        split: {label: counts[(split, label)] for label in LABELS}
        for split in ("train", "val", "val_cal")
    }
    machine_rows = [row for row in rows if row["source_kind"] == "machine_camera_view"]
    report = {
        "schema_version": 1,
        "status": "MACHINE_VIEW_MERGED_DATASET_READY",
        "base": str(base),
        "machine_source": str(machine_source),
        "dataset_root": str(dataset),
        "manifest": str(manifest),
        "manifest_sha256": sha256_file(manifest),
        "labels": list(LABELS),
        "other_cat_samples_present": 0,
        "machine_views_are_train_only": True,
        "machine_test_holdout_reserved": False,
        "final_counts": final_counts,
        "total": len(rows),
        "base_rows": len(rows) - len(machine_rows),
        "machine_rows": len(machine_rows),
        "machine_label_counts": dict(Counter(str(row["label"]) for row in machine_rows)),
        "machine_route_counts": dict(
            Counter(str(row["route_mode"]) for row in machine_rows)
        ),
        "skipped_exact_source_duplicates": skipped_exact_source_duplicates,
        "skipped_existing_view_duplicates": skipped_existing_view_duplicates,
        "base_materialization": dict(materialization),
        "detector_sha256": sha256_file(detector_path),
    }
    (output / "merged_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
