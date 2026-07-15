from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--provisional-manifest",
        type=Path,
        default=ROOT / "data/downloads/baseline_provisional_split/provisional_split_manifest.csv",
    )
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    if output.exists() and not args.resume:
        raise FileExistsError(output)
    parent_manifest = source / "merged_manifest.csv"
    rows = read_csv(parent_manifest)
    provisional = read_csv(args.provisional_manifest)
    excluded_ids = {
        row["sample_id"]
        for row in provisional
        if row["label"] == "not_target" and "other_cat_breed" in row["source_relative_path"]
    }
    kept = [row for row in rows if row["sample_id"] not in excluded_ids]
    excluded = [row for row in rows if row["sample_id"] in excluded_ids]
    dataset_root = output / "one_view_yolo_classify"
    for row in kept:
        src = source / "one_view_yolo_classify" / row["dataset_relative_path"]
        if not src.is_file():
            fallback = Path(row["source_relative_path"])
            if fallback.is_file() and sha256_file(fallback) == row["view_sha256"]:
                src = fallback
            else:
                raise FileNotFoundError(
                    f"missing view and no hash-identical fallback: {row['sample_id']}"
                )
        dst = dataset_root / row["dataset_relative_path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or sha256_file(dst) != row["view_sha256"]:
            shutil.copy2(src, dst)
        if sha256_file(dst) != row["view_sha256"]:
            raise RuntimeError(f"copied hash mismatch: {dst}")
    manifest = output / "merged_manifest.csv"
    with manifest.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(kept)
    counts = Counter((row["split"], row["label"]) for row in kept)
    final_counts = {
        split: {
            label: counts[(split, label)]
            for label in ("ragdoll", "singapura", "persian", "sphynx", "pallas", "not_target")
        }
        for split in ("train", "val", "val_cal")
    }
    report = {
        "schema_version": 1,
        "status": "NO_OTHER_CAT_DATASET_READY",
        "parent_dataset": str(source),
        "parent_manifest_sha256": sha256_file(parent_manifest),
        "dataset_root": str(dataset_root),
        "manifest": str(manifest),
        "manifest_sha256": sha256_file(manifest),
        "rows": len(kept),
        "excluded_other_cat_count": len(excluded),
        "excluded_sample_ids": sorted(row["sample_id"] for row in excluded),
        "final_counts": final_counts,
    }
    (output / "merged_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
