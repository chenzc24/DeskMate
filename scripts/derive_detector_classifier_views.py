"""Generate deterministic B-D01 classifier crops after a frozen parent split."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
import time
import tomllib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from deskmate_baseline.contracts import FramePacket, INTERNAL_LABELS, REPORTABLE_LABELS  # noqa: E402
from deskmate_baseline.localization import (  # noqa: E402
    UltralyticsCatLocalizerBackend,
    route_classification_roi,
)


CLASS_DIRS = {label: f"{index}_{label}" for index, label in enumerate(INTERNAL_LABELS)}
SPLIT_DIRS = {"train": "train", "val_select": "val", "val_cal": "val_cal"}
VIEW_FIELDS = (
    "view_id",
    "parent_image_id",
    "label",
    "split",
    "view_kind",
    "selected_for_folder_training",
    "source_relative_path",
    "view_relative_path",
    "view_sha256",
    "detector_model_id",
    "detector_weight_sha256",
    "ultralytics_version",
    "cat_class_id",
    "normalized_xyxy",
    "detector_confidence",
    "padding_ratio",
    "crop_clamped",
    "quality_result",
    "detector_status",
    "detector_box_count",
    "selection_reason",
    "generator_config_sha256",
    "generated_at",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=VIEW_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in VIEW_FIELDS} for row in rows)


def project_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_config(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        config = tomllib.load(handle)
    if int(config.get("schema_version", 0)) != 1:
        raise ValueError("unsupported derived-view config schema")
    if config["views"]["strategy"] != "one_view_per_parent":
        raise ValueError("handoff requires one_view_per_parent")
    if int(config["training"]["selected_views_per_parent"]) != 1:
        raise ValueError("exactly one selected view per parent is required")
    return config


def negative_source_datasets(path: Path) -> dict[str, str]:
    return {
        row["image_id"]: row["source_dataset"]
        for row in read_csv(path)
        if row["label"] == "not_target"
    }


def resolve_parent_source(
    parent: dict[str, str], *, target_root: Path, negative_root: Path
) -> Path:
    root = target_root if parent["source_kind"] == "human_screened_intake" else negative_root
    return root / parent["source_relative_path"]


def _view_row(
    *,
    view_id: str,
    parent: dict[str, str],
    kind: str,
    selected: bool,
    source_relative_path: str,
    view_relative_path: str,
    view_sha256: str,
    detector: dict[str, Any],
    box: Any | None,
    padding_ratio: float,
    clamped: bool,
    quality_result: str,
    detector_status: str,
    box_count: int,
    selection_reason: str,
    config_sha256: str,
    generated_at: str,
) -> dict[str, Any]:
    return {
        "view_id": view_id,
        "parent_image_id": parent["sample_id"],
        "label": parent["label"],
        "split": parent["split"],
        "view_kind": kind,
        "selected_for_folder_training": str(bool(selected)).lower(),
        "source_relative_path": source_relative_path,
        "view_relative_path": view_relative_path,
        "view_sha256": view_sha256,
        "detector_model_id": detector["model_id"],
        "detector_weight_sha256": detector["weight_sha256"],
        "ultralytics_version": detector["ultralytics_version"],
        "cat_class_id": detector["cat_class_id"],
        "normalized_xyxy": "|".join(f"{value:.8f}" for value in box.xyxy) if box else "",
        "detector_confidence": f"{box.confidence:.8f}" if box else "",
        "padding_ratio": f"{padding_ratio:.6f}" if kind == "bd01_crop" else "",
        "crop_clamped": str(bool(clamped)).lower() if kind == "bd01_crop" else "",
        "quality_result": quality_result,
        "detector_status": detector_status,
        "detector_box_count": box_count,
        "selection_reason": selection_reason,
        "generator_config_sha256": config_sha256,
        "generated_at": generated_at,
    }


def derive_views(
    *,
    config_path: Path,
    output_root: Path | None = None,
    backend: Any | None = None,
) -> dict[str, Any]:
    import cv2

    config = load_config(config_path)
    paths = config["paths"]
    base_manifest = project_path(paths["base_split_manifest"])
    base_root = project_path(paths["base_dataset_root"])
    target_source_root = project_path(paths["target_source_root"])
    negative_source_root = project_path(paths["negative_source_root"])
    negative_manifest = project_path(paths["negative_source_manifest"])
    selected_output = output_root or project_path(paths["output_root"])
    if selected_output.exists():
        raise FileExistsError(f"output already exists: {selected_output}")
    parents = read_csv(base_manifest)
    if len({row["sample_id"] for row in parents}) != len(parents):
        raise ValueError("parent split contains duplicate sample IDs")
    negative_datasets = negative_source_datasets(negative_manifest)
    detector_config = config["detector"]
    views_config = config["views"]
    checkpoint = project_path(detector_config["checkpoint"])
    weight_hash = sha256_file(checkpoint)
    if weight_hash != str(detector_config["expected_sha256"]).casefold():
        raise RuntimeError("B-D01 checksum mismatch")
    owns_backend = backend is None
    if backend is None:
        backend = UltralyticsCatLocalizerBackend(
            checkpoint=checkpoint,
            model_id=str(detector_config["model_id"]),
            device=detector_config["device"],
            imgsz=int(detector_config["imgsz"]),
            confidence_threshold=float(detector_config["confidence_threshold"]),
            minimum_box_area_ratio=float(detector_config["minimum_box_area_ratio"]),
            maximum_candidates=int(detector_config["maximum_candidates"]),
            maximum_frame_age_ms=float(detector_config["maximum_frame_age_ms"]),
        )
    backend.load()
    backend.warmup()
    import ultralytics

    detector_evidence = {
        "model_id": str(detector_config["model_id"]),
        "weight_sha256": weight_hash,
        "ultralytics_version": ultralytics.__version__,
        "cat_class_id": int(backend.cat_class_id),
    }
    config_hash = sha256_file(config_path)
    generated_at = str(config["generated_at"])
    padding_ratio = float(views_config["padding_ratio"])
    minimum_width = int(views_config["minimum_crop_width"])
    minimum_height = int(views_config["minimum_crop_height"])
    jpeg_quality = int(views_config["jpeg_quality"])
    known_other_breed = str(views_config["known_other_breed_source_dataset"])
    selected_output.mkdir(parents=True)
    view_rows: list[dict[str, Any]] = []
    coverage: dict[str, Counter[str]] = defaultdict(Counter)
    selected_counts: dict[str, Counter[str]] = defaultdict(Counter)
    selected_hashes: list[str] = []
    try:
        for frame_id, parent in enumerate(
            sorted(parents, key=lambda row: (INTERNAL_LABELS.index(row["label"]), row["sample_id"]))
        ):
            if parent["label"] not in INTERNAL_LABELS or parent["split"] not in SPLIT_DIRS:
                raise ValueError(f"invalid parent row: {parent['sample_id']}")
            source = resolve_parent_source(
                parent,
                target_root=target_source_root,
                negative_root=negative_source_root,
            )
            if not source.is_file() or sha256_file(source) != parent["exact_sha256"]:
                raise RuntimeError(f"parent source mismatch: {parent['sample_id']}")
            image = cv2.imread(str(source), cv2.IMREAD_COLOR)
            if image is None or image.ndim != 3 or image.shape[2] != 3:
                raise ValueError(f"could not decode parent: {parent['sample_id']}")
            captured_at = time.time_ns()
            packet = FramePacket(
                frame_id=frame_id,
                captured_at_ns=captured_at,
                image_bgr=image,
                source="offline_frozen_parent",
                width=int(image.shape[1]),
                height=int(image.shape[0]),
            )
            observation = backend.infer(packet)
            boxes = tuple(observation.boxes) if observation.valid else ()
            if not observation.valid:
                detector_status = "invalid"
            elif not boxes:
                detector_status = "miss"
            elif len(boxes) == 1:
                detector_status = "hit"
            else:
                detector_status = "multi_box"
            coverage[parent["label"]][detector_status] += 1
            box = boxes[0] if boxes else None
            source_dataset = negative_datasets.get(parent["source_image_id"], "")
            use_crop = bool(box) and (
                parent["label"] in REPORTABLE_LABELS
                or (
                    parent["label"] == "not_target"
                    and source_dataset == known_other_breed
                )
            )
            crop_image = None
            clamped = False
            quality = "not_applicable"
            if use_crop:
                routed = route_classification_roi(
                    packet,
                    observation,
                    box_is_stable=True,
                    padding_ratio=padding_ratio,
                )
                crop_image = routed.image_bgr
                left, top, right, bottom = routed.pixel_xyxy
                clamped = left == 0 or top == 0 or right == packet.width or bottom == packet.height
                if crop_image.shape[1] < minimum_width or crop_image.shape[0] < minimum_height:
                    use_crop = False
                    crop_image = None
                    quality = "rejected_small_crop"
                else:
                    quality = "passed"
            original_selected = not use_crop
            original_reason = (
                "detector_miss_or_invalid_fallback"
                if not box
                else "background_original_policy"
                if parent["label"] == "not_target" and source_dataset != known_other_breed
                else "crop_quality_fallback"
                if not use_crop
                else "crop_selected_instead"
            )
            view_rows.append(
                _view_row(
                    view_id=f"{parent['sample_id']}--original",
                    parent=parent,
                    kind="original",
                    selected=original_selected,
                    source_relative_path=parent["source_relative_path"],
                    view_relative_path=parent["source_relative_path"],
                    view_sha256=parent["exact_sha256"],
                    detector=detector_evidence,
                    box=box,
                    padding_ratio=padding_ratio,
                    clamped=False,
                    quality_result="passed",
                    detector_status=detector_status,
                    box_count=len(boxes),
                    selection_reason=original_reason,
                    config_sha256=config_hash,
                    generated_at=generated_at,
                )
            )
            selected_source = source
            selected_kind = "original"
            selected_hash = parent["exact_sha256"]
            if use_crop and crop_image is not None:
                crop_relative = (
                    Path("derived")
                    / "bd01_crops"
                    / SPLIT_DIRS[parent["split"]]
                    / CLASS_DIRS[parent["label"]]
                    / f"{parent['sample_id']}--bd01.jpg"
                )
                crop_path = selected_output / crop_relative
                crop_path.parent.mkdir(parents=True, exist_ok=True)
                if not cv2.imwrite(
                    str(crop_path), crop_image, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
                ):
                    raise RuntimeError(f"failed to write crop: {crop_relative}")
                crop_hash = sha256_file(crop_path)
                view_rows.append(
                    _view_row(
                        view_id=f"{parent['sample_id']}--bd01",
                        parent=parent,
                        kind="bd01_crop",
                        selected=True,
                        source_relative_path=parent["source_relative_path"],
                        view_relative_path=crop_relative.as_posix(),
                        view_sha256=crop_hash,
                        detector=detector_evidence,
                        box=box,
                        padding_ratio=padding_ratio,
                        clamped=clamped,
                        quality_result=quality,
                        detector_status=detector_status,
                        box_count=len(boxes),
                        selection_reason="target_or_known_other_breed_primary_crop",
                        config_sha256=config_hash,
                        generated_at=generated_at,
                    )
                )
                selected_source = crop_path
                selected_kind = "bd01_crop"
                selected_hash = crop_hash
            destination_relative = (
                Path("one_view_yolo_classify")
                / SPLIT_DIRS[parent["split"]]
                / CLASS_DIRS[parent["label"]]
                / f"{parent['sample_id']}.jpg"
            )
            destination = selected_output / destination_relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(selected_source, destination)
            if sha256_file(destination) != selected_hash:
                raise RuntimeError(f"selected view hash mismatch: {parent['sample_id']}")
            selected_hashes.append(f"{parent['sample_id']}\0{selected_hash}")
            selected_counts[parent["label"]][selected_kind] += 1
    finally:
        if owns_backend:
            backend.close()

    view_manifest = selected_output / "view_manifest.csv"
    write_csv(view_manifest, view_rows)
    selected_rows = [row for row in view_rows if row["selected_for_folder_training"] == "true"]
    selected_by_parent = Counter(row["parent_image_id"] for row in selected_rows)
    invalid_selected = [parent for parent, count in selected_by_parent.items() if count != 1]
    if len(selected_by_parent) != len(parents) or invalid_selected:
        raise RuntimeError("one-view-per-parent invariant failed")
    selected_snapshot = hashlib.sha256("\n".join(selected_hashes).encode("utf-8")).hexdigest()
    report: dict[str, Any] = {
        "schema_version": 1,
        "status": "DETECTOR_DERIVED_ONE_VIEW_DATASET_READY",
        "freeze_id": config["freeze_id"],
        "generated_at": generated_at,
        "official_gate_b1_ready": False,
        "provisional_training_data_ready": True,
        "risk_scope": "development_only_not_final_release",
        "parent_count": len(parents),
        "view_count": len(view_rows),
        "selected_view_count": len(selected_rows),
        "selected_views_per_parent": 1,
        "class_order": list(INTERNAL_LABELS),
        "detector": detector_evidence,
        "coverage": {label: dict(sorted(coverage[label].items())) for label in INTERNAL_LABELS},
        "selected_kind_counts": {
            label: dict(sorted(selected_counts[label].items())) for label in INTERNAL_LABELS
        },
        "multi_box_review_state": "deferred_provisional_primary_selected",
        "background_false_positive_crop_policy": "original_unless_known_other_breed",
        "materialized_dataset_root": "one_view_yolo_classify",
        "base_split_manifest_sha256": sha256_file(base_manifest),
        "config_sha256": config_hash,
        "view_manifest_sha256": sha256_file(view_manifest),
        "manifest_sha256": sha256_file(view_manifest),
        "selected_snapshot_sha256": selected_snapshot,
    }
    (selected_output / "derived_view_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "baseline_derived_views.toml",
    )
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    report = derive_views(config_path=args.config, output_root=args.output_root)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
