from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET_LABELS = ("ragdoll", "singapura", "persian", "sphynx", "pallas")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def materialize(source: Path, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if sha256_file(source) != sha256_file(destination):
            raise RuntimeError(f"existing target differs: {destination}")
        return "existing"
    try:
        os.link(source, destination)
        return "hardlink"
    except OSError:
        shutil.copy2(source, destination)
        return "copy"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / "data/downloads/baseline_merged_gapfill_20260715",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/downloads/baseline_target5_20260715",
    )
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    source_dataset = source / "one_view_yolo_classify"
    target_dataset = output / "one_view_yolo_classify"
    with (source / "merged_manifest.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    kept = [row for row in rows if row["label"] in TARGET_LABELS]
    methods: Counter[str] = Counter()
    for row in kept:
        relative = Path(row["dataset_relative_path"])
        source_path = source_dataset / relative
        destination = target_dataset / relative
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        methods[materialize(source_path, destination)] += 1
    output.mkdir(parents=True, exist_ok=True)
    manifest = output / "target5_manifest.csv"
    with manifest.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(kept[0]))
        writer.writeheader()
        writer.writerows(kept)
    counts = Counter((row["split"], row["label"]) for row in kept)
    final_counts = {
        split: {label: counts[(split, label)] for label in TARGET_LABELS}
        for split in ("train", "val", "val_cal")
    }
    report = {
        "schema_version": 1,
        "status": "TARGET5_DATASET_READY",
        "source_root": str(source),
        "dataset_root": str(target_dataset),
        "manifest": str(manifest),
        "manifest_sha256": sha256_file(manifest),
        "labels": list(TARGET_LABELS),
        "not_target_present": False,
        "final_counts": final_counts,
        "total": len(kept),
        "materialization": dict(methods),
        "robot_diagnostic_images_in_training": 0,
    }
    (output / "target5_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
