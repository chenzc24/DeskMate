from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import cv2


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from deskmate_baseline.contracts import FramePacket  # noqa: E402
from deskmate_baseline.localization import (  # noqa: E402
    UltralyticsCatLocalizerBackend,
    route_classification_roi,
)


CLASS_DIRS = {
    "ragdoll": "0_ragdoll",
    "singapura": "1_singapura",
    "persian": "2_persian",
    "sphynx": "3_sphynx",
    "pallas": "4_pallas",
    "not_target": "5_not_target",
}
SPLITS = ("train", "val", "val_cal")
ADDITIONAL_LABELS = ("singapura", "pallas")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_filtered_manifest(folder: Path, label: str) -> list[dict[str, str]]:
    with (folder / "manifest.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    remaining = {path.name for path in folder.iterdir() if path.is_file() and path.name != "manifest.csv"}
    selected = [row for row in rows if row["review_filename"] in remaining]
    if len(selected) != len(remaining):
        known = {row["review_filename"] for row in selected}
        raise ValueError(f"{label}: files missing from manifest: {sorted(remaining - known)}")
    for row in selected:
        source = folder / row["review_filename"]
        if row["label"] != label:
            raise ValueError(f"label mismatch: {source}")
        if sha256_file(source) != row["exact_sha256"].casefold():
            raise ValueError(f"hash mismatch: {source}")
    return selected


def stable_group_rank(row: dict[str, str], seed: int) -> str:
    group = row.get("source_group_id") or row["image_id"]
    return hashlib.sha256(f"{seed}:{group}".encode("utf-8")).hexdigest()


def assign_splits(rows: list[dict[str, str]], seed: int) -> dict[str, str]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get("source_group_id") or row["image_id"]].append(row)
    ordered = sorted(groups.items(), key=lambda item: stable_group_rank(item[1][0], seed))
    total = len(rows)
    targets = {"train": round(total * 0.85), "val": round(total * 0.10)}
    targets["val_cal"] = total - targets["train"] - targets["val"]
    assignment: dict[str, str] = {}
    counts = Counter()
    for group, members in ordered:
        split = min(SPLITS, key=lambda name: (counts[name] / max(targets[name], 1), SPLITS.index(name)))
        for row in members:
            assignment[row["image_id"]] = split
        counts[split] += len(members)
    return assignment


def copy_base(base: Path, dataset_root: Path, manifest_rows: list[dict[str, str]]) -> None:
    for split in SPLITS:
        for label, class_dir in CLASS_DIRS.items():
            source_dir = base / split / class_dir
            if not source_dir.is_dir():
                raise FileNotFoundError(source_dir)
            destination = dataset_root / split / class_dir
            destination.mkdir(parents=True, exist_ok=True)
            for source in sorted(path for path in source_dir.iterdir() if path.is_file()):
                target = destination / source.name
                shutil.copy2(source, target)
                manifest_rows.append(
                    {
                        "sample_id": source.stem,
                        "label": label,
                        "split": split,
                        "dataset_relative_path": target.relative_to(dataset_root).as_posix(),
                        "source_kind": "existing_detector_view",
                        "source_image_id": source.stem,
                        "source_group_id": "",
                        "source_relative_path": str(source),
                        "source_sha256": sha256_file(source),
                        "view_kind": "existing_frozen_view",
                        "view_sha256": sha256_file(target),
                        "detector_box_count": "",
                        "detector_confidence": "",
                        "route_reason": "existing_dataset",
                    }
                )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--additional", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260715)
    args = parser.parse_args()
    base = args.base.resolve()
    additional = args.additional.resolve()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    dataset_root = output / "one_view_yolo_classify"
    manifest_rows: list[dict[str, str]] = []
    copy_base(base, dataset_root, manifest_rows)

    checkpoint = ROOT / "models" / "yolo26s.pt"
    backend = UltralyticsCatLocalizerBackend(
        checkpoint=checkpoint,
        device=0,
        imgsz=640,
        confidence_threshold=0.25,
        minimum_box_area_ratio=0.02,
        maximum_candidates=5,
        candidate_deduplication_iou_threshold=0.85,
        maximum_frame_age_ms=500.0,
    )
    backend.load()
    backend.warmup()
    route_counts = Counter()
    additions = Counter()
    frame_id = 0
    for label_index, label in enumerate(ADDITIONAL_LABELS):
        folder = additional / label
        rows = read_filtered_manifest(folder, label)
        assignments = assign_splits(rows, args.seed + label_index)
        for row in sorted(rows, key=lambda item: item["image_id"]):
            source = folder / row["review_filename"]
            image = cv2.imread(str(source), cv2.IMREAD_COLOR)
            if image is None or image.ndim != 3 or image.shape[2] != 3:
                raise ValueError(f"cannot decode: {source}")
            captured_at = time.time_ns()
            packet = FramePacket(
                frame_id=frame_id,
                captured_at_ns=captured_at,
                image_bgr=image,
                source="additional_human_reviewed",
                width=int(image.shape[1]),
                height=int(image.shape[0]),
            )
            observation = backend.infer(packet)
            boxes = tuple(observation.boxes) if observation.valid else ()
            if boxes:
                routed = route_classification_roi(
                    packet,
                    observation,
                    box_is_stable=True,
                    padding_ratio=0.15,
                    minimum_padded_short_side_pixels=32,
                )
                selected = routed.image_bgr
                view_kind = routed.mode
                route_reason = routed.route_reason
                confidence = routed.source_confidence
            else:
                selected = image
                view_kind = "original"
                route_reason = "detector_miss_or_invalid_fallback"
                confidence = None
            split = assignments[row["image_id"]]
            class_dir = CLASS_DIRS[label]
            filename = f"additional-{label}-{row['image_id']}.jpg"
            target = dataset_root / split / class_dir / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            if not cv2.imwrite(str(target), selected, [cv2.IMWRITE_JPEG_QUALITY, 95]):
                raise RuntimeError(f"failed to write: {target}")
            manifest_rows.append(
                {
                    "sample_id": Path(filename).stem,
                    "label": label,
                    "split": split,
                    "dataset_relative_path": target.relative_to(dataset_root).as_posix(),
                    "source_kind": row["source_kind"],
                    "source_image_id": row["image_id"],
                    "source_group_id": row["source_group_id"],
                    "source_relative_path": str(source),
                    "source_sha256": row["exact_sha256"],
                    "view_kind": view_kind,
                    "view_sha256": sha256_file(target),
                    "detector_box_count": str(len(boxes)),
                    "detector_confidence": "" if confidence is None else f"{confidence:.8f}",
                    "route_reason": route_reason,
                }
            )
            route_counts[(label, view_kind)] += 1
            additions[(label, split)] += 1
            frame_id += 1
    fields = list(manifest_rows[0])
    manifest = output / "merged_manifest.csv"
    with manifest.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(manifest_rows)
    final_counts: dict[str, dict[str, int]] = {}
    for split in SPLITS:
        final_counts[split] = {
            label: len(list((dataset_root / split / class_dir).glob("*")))
            for label, class_dir in CLASS_DIRS.items()
        }
    report = {
        "schema_version": 1,
        "status": "MERGED_DATASET_READY",
        "seed": args.seed,
        "base": str(base),
        "additional": str(additional),
        "dataset_root": str(dataset_root),
        "manifest": str(manifest),
        "manifest_sha256": sha256_file(manifest),
        "base_rows": len(manifest_rows) - sum(additions.values()),
        "additional_rows": sum(additions.values()),
        "additional_split_counts": {f"{label}/{split}": count for (label, split), count in sorted(additions.items())},
        "additional_route_counts": {f"{label}/{route}": count for (label, route), count in sorted(route_counts.items())},
        "final_counts": final_counts,
        "detector": {
            "checkpoint": str(checkpoint),
            "sha256": sha256_file(checkpoint),
            "confidence_threshold": 0.25,
            "minimum_box_area_ratio": 0.02,
            "padding_ratio": 0.15,
            "minimum_padded_short_side_pixels": 32,
        },
    }
    (output / "merged_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
