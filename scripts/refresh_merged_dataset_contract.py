from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LABELS = ("ragdoll", "singapura", "persian", "sphynx", "pallas", "not_target")
CLASS_DIRS = {label: f"{index}_{label}" for index, label in enumerate(LABELS)}
SPLITS = ("train", "val", "val_cal")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--remove-other-cat", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    dataset_root = root / "one_view_yolo_classify"
    manifest_path = root / "merged_manifest.csv"
    report_path = root / "merged_report.json"
    original_rows = read_csv(manifest_path)
    row_by_path = {row["dataset_relative_path"]: row for row in original_rows}
    provisional = read_csv(
        ROOT / "data/downloads/baseline_provisional_split/provisional_split_manifest.csv"
    )
    other_cat_ids = {
        row["sample_id"]
        for row in provisional
        if row["label"] == "not_target"
        and "other_cat_breed" in row["source_relative_path"]
    }
    contracted_other_cat_ids = {
        row["sample_id"] for row in original_rows if row["sample_id"] in other_cat_ids
    }
    removed: list[str] = []
    if args.remove_other_cat:
        for path in dataset_root.rglob("*"):
            if path.is_file() and path.stem in other_cat_ids:
                path.unlink()
                removed.append(path.stem)
    actual_paths = sorted(
        path
        for path in dataset_root.rglob("*")
        if path.is_file() and path.suffix.casefold() in {".jpg", ".jpeg", ".png"}
    )
    kept: list[dict[str, str]] = []
    for path in actual_paths:
        relative = path.relative_to(dataset_root).as_posix()
        if relative not in row_by_path:
            raise ValueError(f"dataset file is absent from manifest: {relative}")
        row = row_by_path[relative]
        if row["sample_id"] in other_cat_ids:
            raise RuntimeError(f"other-cat sample remains: {relative}")
        digest = sha256_file(path)
        if digest != row["view_sha256"]:
            raise RuntimeError(f"view hash mismatch: {relative}")
        kept.append(row)
    counts = Counter((row["split"], row["label"]) for row in kept)
    additional_rows = [
        row for row in kept if row["source_kind"] != "existing_detector_view"
    ]
    additional_split_counts = Counter(
        (row["label"], row["split"]) for row in additional_rows
    )
    additional_route_counts = Counter(
        (row["label"], row["view_kind"]) for row in additional_rows
    )
    final_counts = {
        split: {label: counts[(split, label)] for label in LABELS}
        for split in SPLITS
    }
    with manifest_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(original_rows[0]))
        writer.writeheader()
        writer.writerows(kept)
    prior_report = json.loads(report_path.read_text(encoding="utf-8"))
    report = {
        **prior_report,
        "status": "NO_OTHER_CAT_DATASET_READY",
        "dataset_root": str(dataset_root),
        "manifest": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "base_rows": sum(row["source_kind"] == "existing_detector_view" for row in kept),
        "additional_rows": len(additional_rows),
        "additional_split_counts": {
            f"{label}/{split}": count
            for (label, split), count in sorted(additional_split_counts.items())
        },
        "additional_route_counts": {
            f"{label}/{route}": count
            for (label, route), count in sorted(additional_route_counts.items())
        },
        "final_counts": final_counts,
        "contract": {
            "not_target_excludes_other_cat_breed": True,
            "other_cat_samples_present": 0,
        },
        "contract_refresh": {
            "rows_before": len(original_rows),
            "rows_after": len(kept),
            "missing_or_human_removed_rows": len(original_rows)
            - len(kept)
            - len(contracted_other_cat_ids),
            "removed_other_cat_sample_ids": sorted(contracted_other_cat_ids),
        },
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
