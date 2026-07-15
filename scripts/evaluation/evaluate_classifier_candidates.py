#!/usr/bin/env python3
"""Compare current and hardened classifiers through one frozen ROI route."""

from __future__ import annotations

import csv
import hashlib
import json
import statistics
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from deskmate_baseline.domain.contracts import INTERNAL_LABELS, FramePacket  # noqa: E402
from deskmate_baseline.perception.inference import UltralyticsClassificationBackend  # noqa: E402
from deskmate_baseline.perception.localization import (  # noqa: E402
    UltralyticsCatLocalizerBackend,
    route_classification_roi,
)


OUTPUT = ROOT / "data" / "downloads" / "baseline_classifier_hardening" / "evaluation"
DETECTOR = ROOT / "models" / "yolo26s.pt"
MODEL_PATHS = {
    "current": ROOT
    / "runs/baseline_provisional/b-m01-provisional-bd01-oneview-seed-20260715/weights/best.pt",
    "balanced_oneview": ROOT
    / "runs/baseline_classifier_hardening/b-m01-balanced_oneview-seed-20260715/weights/best.pt",
    "balanced_print": ROOT
    / "runs/baseline_classifier_hardening/b-m01-balanced_print-seed-20260715/weights/best.pt",
    "soup_b50_p50": ROOT / "runs/baseline_classifier_hardening/soups/b50_p50.pt",
    "soup_b40_p60": ROOT / "runs/baseline_classifier_hardening/soups/b40_p60.pt",
    "soup_b45_p55": ROOT / "runs/baseline_classifier_hardening/soups/b45_p55.pt",
    "soup_b55_p45": ROOT / "runs/baseline_classifier_hardening/soups/b55_p45.pt",
    "soup_b60_p40": ROOT / "runs/baseline_classifier_hardening/soups/b60_p40.pt",
    "soup_c34_b33_p33": ROOT / "runs/baseline_classifier_hardening/soups/c34_b33_p33.pt",
    "soup_c50_b25_p25": ROOT / "runs/baseline_classifier_hardening/soups/c50_b25_p25.pt",
    "soup_c60_b20_p20": ROOT / "runs/baseline_classifier_hardening/soups/c60_b20_p20.pt",
    "soup_c70_b15_p15": ROOT / "runs/baseline_classifier_hardening/soups/c70_b15_p15.pt",
}
SOURCE_ROOTS = (
    ROOT / "data" / "downloads" / "cat_processed",
    ROOT / "data" / "downloads" / "phase1_candidates",
)
ROBOT_LABELS = (
    "sphynx",
    "sphynx",
    "sphynx",
    "persian",
    "ragdoll",
    "persian",
    "singapura",
    "pallas",
    "pallas",
)
DISPLAY_MODELS = ("current", "soup_b50_p50")


@dataclass(frozen=True)
class Sample:
    sample_id: str
    group: str
    split: str
    label: str
    path: Path


def read_image(path: Path) -> np.ndarray:
    image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"could not decode image: {path}")
    return image


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_source(relative: str) -> Path:
    matches = [root / relative for root in SOURCE_ROOTS if (root / relative).is_file()]
    if len(matches) != 1:
        raise FileNotFoundError(f"expected one source for {relative}; got {matches}")
    return matches[0]


def load_samples() -> list[Sample]:
    validation_csv = (
        ROOT
        / "data/downloads/baseline_full_pipeline_validation_only/predictions.csv"
    )
    with validation_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        validation = list(csv.DictReader(handle))
    samples = [
        Sample(
            sample_id=row["sample_id"],
            group="validation",
            split=row["split"],
            label=row["label"],
            path=resolve_source(row["source_relative_path"]),
        )
        for row in validation
    ]
    if len(samples) != 419 or len({sample.sample_id for sample in samples}) != 419:
        raise RuntimeError("validation snapshot is not the frozen 419 unique parents")
    camera = sorted((ROOT / "data/downloads/Camera").glob("*"))
    if len(camera) != len(ROBOT_LABELS):
        raise RuntimeError("robot still snapshot changed")
    samples.extend(
        Sample(f"robot-{index:02d}", "robot", "robot", label, path)
        for index, (path, label) in enumerate(zip(camera, ROBOT_LABELS), 1)
    )
    return samples


def classify(
    backend: UltralyticsClassificationBackend,
    image: np.ndarray,
    *,
    frame_id: int,
) -> tuple[Any, float]:
    packet = FramePacket(
        frame_id=frame_id,
        captured_at_ns=time.time_ns(),
        image_bgr=image,
        source="classifier_candidate_roi",
        width=int(image.shape[1]),
        height=int(image.shape[0]),
    )
    started = time.perf_counter_ns()
    observation = backend.infer(packet, "wide")
    elapsed = (time.perf_counter_ns() - started) / 1_000_000
    if not observation.valid:
        raise RuntimeError(observation.reason)
    return observation, elapsed


def metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for model_id in MODEL_PATHS:
        model_rows = [row for row in rows if row["model_id"] == model_id]
        result[model_id] = {}
        for group_name, selected in (
            ("validation_all", [row for row in model_rows if row["group"] == "validation"]),
            ("val_select", [row for row in model_rows if row["split"] == "val_select"]),
            ("val_cal", [row for row in model_rows if row["split"] == "val_cal"]),
            ("robot", [row for row in model_rows if row["group"] == "robot"]),
        ):
            per_class = {}
            f1_values = []
            for label in INTERNAL_LABELS:
                true_positive = sum(
                    row["label"] == label and row["prediction"] == label for row in selected
                )
                false_positive = sum(
                    row["label"] != label and row["prediction"] == label for row in selected
                )
                false_negative = sum(
                    row["label"] == label and row["prediction"] != label for row in selected
                )
                support = sum(row["label"] == label for row in selected)
                precision = (
                    true_positive / (true_positive + false_positive)
                    if true_positive + false_positive
                    else 0.0
                )
                recall = true_positive / support if support else None
                f1 = (
                    2 * precision * recall / (precision + recall)
                    if recall is not None and precision + recall
                    else 0.0
                )
                if support:
                    f1_values.append(f1)
                per_class[label] = {
                    "support": support,
                    "correct": true_positive,
                    "precision": precision,
                    "recall": recall,
                    "f1": f1 if support else None,
                }
            result[model_id][group_name] = {
                "count": len(selected),
                "correct": sum(row["correct"] for row in selected),
                "accuracy": sum(row["correct"] for row in selected) / len(selected),
                "macro_f1_supported_classes": statistics.fmean(f1_values),
                "per_class": per_class,
                "prediction_counts": dict(Counter(row["prediction"] for row in selected)),
            }
    return result


def render_robot_sheet(rows: list[dict[str, Any]], samples: list[Sample]) -> None:
    lookup = {(row["sample_id"], row["model_id"]): row for row in rows}
    tiles = []
    for sample in (item for item in samples if item.group == "robot"):
        image = cv2.resize(read_image(sample.path), (480, 360))
        footer = np.full((100, 480, 3), 245, dtype=np.uint8)
        lines = [f"GT visible print: {sample.label}"]
        for model_id in DISPLAY_MODELS:
            row = lookup[(sample.sample_id, model_id)]
            lines.append(
                f"{model_id}: {row['prediction']} {float(row['confidence']):.3f}"
            )
        for index, line in enumerate(lines):
            color = (10, 120, 10) if index and line.split(": ", 1)[1].startswith(sample.label) else (20, 20, 20)
            cv2.putText(
                footer,
                line,
                (8, 25 + index * 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                1,
                cv2.LINE_AA,
            )
        tiles.append(np.vstack((image, footer)))
    blank = np.full_like(tiles[0], 255)
    grid = []
    for start in range(0, len(tiles), 3):
        chunk = tiles[start : start + 3]
        grid.append(np.hstack(chunk + [blank] * (3 - len(chunk))))
    cv2.imwrite(str(OUTPUT / "robot_candidate_comparison.jpg"), np.vstack(grid))


def main() -> int:
    missing = [str(path) for path in (DETECTOR, *MODEL_PATHS.values()) if not path.is_file()]
    if missing:
        raise FileNotFoundError(missing)
    samples = load_samples()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    detector = UltralyticsCatLocalizerBackend(
        checkpoint=DETECTOR,
        device=0,
        imgsz=640,
        confidence_threshold=0.25,
        minimum_box_area_ratio=0.01,
        maximum_candidates=5,
        candidate_deduplication_iou_threshold=0.85,
        maximum_frame_age_ms=60_000.0,
    )
    classifiers = {
        model_id: UltralyticsClassificationBackend(
            checkpoint=path,
            device=0,
            imgsz=224,
            temperature=1.0,
            maximum_frame_age_ms=60_000.0,
        )
        for model_id, path in MODEL_PATHS.items()
    }
    detector.load()
    detector.warmup()
    for backend in classifiers.values():
        backend.load()
        backend.warmup()
    rows: list[dict[str, Any]] = []
    frame_id = 1
    try:
        for sample in samples:
            image = read_image(sample.path)
            frame = FramePacket(
                frame_id=frame_id,
                captured_at_ns=time.time_ns(),
                image_bgr=image,
                source=str(sample.path.relative_to(ROOT)),
                width=int(image.shape[1]),
                height=int(image.shape[0]),
            )
            frame_id += 1
            localization = detector.infer(frame)
            if not localization.valid:
                raise RuntimeError(localization.reason)
            roi = route_classification_roi(
                frame,
                localization,
                box_is_stable=True,
                padding_ratio=0.15,
                fallback_center_scale=0.8,
                minimum_padded_short_side_pixels=64,
            )
            for model_id, backend in classifiers.items():
                observation, latency_ms = classify(backend, roi.image_bgr, frame_id=frame_id)
                frame_id += 1
                rows.append(
                    {
                        "sample_id": sample.sample_id,
                        "group": sample.group,
                        "split": sample.split,
                        "label": sample.label,
                        "source_relative_path": str(sample.path.relative_to(ROOT)),
                        "route": roi.mode,
                        "route_reason": roi.route_reason,
                        "model_id": model_id,
                        "prediction": observation.label,
                        "confidence": observation.calibrated_confidence,
                        "margin": observation.margin,
                        "correct": observation.label == sample.label,
                        "classifier_ms": latency_ms,
                    }
                )
    finally:
        detector.close()
        for backend in classifiers.values():
            backend.close()
    with (OUTPUT / "predictions.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "schema_version": 1,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "CLASSIFIER_CANDIDATE_EVALUATION_COMPLETE",
        "sample_roles": {
            "validation": "frozen_val_select_plus_val_cal_419_parents",
            "robot": "nine_static_stills_visible_printed_labels_not_release_accuracy",
        },
        "route": {
            "detector_confidence": 0.25,
            "minimum_box_area_ratio": 0.01,
            "minimum_padded_short_side_pixels": 64,
            "deduplication_iou": 0.85,
        },
        "models": {
            model_id: {"path": str(path.relative_to(ROOT)), "sha256": sha256_file(path)}
            for model_id, path in MODEL_PATHS.items()
        },
        "metrics": metrics(rows),
        "latency_ms": {
            model_id: {
                "mean": statistics.fmean(
                    row["classifier_ms"] for row in rows if row["model_id"] == model_id
                ),
                "p95": sorted(
                    row["classifier_ms"] for row in rows if row["model_id"] == model_id
                )[int(0.95 * sum(row["model_id"] == model_id for row in rows)) - 1],
            }
            for model_id in MODEL_PATHS
        },
        "limitations": [
            "raw_probabilities_are_uncalibrated",
            "robot_stills_were_seen_during_candidate_design_and_are_not_final_test",
            "static_images_do_not_validate_temporal_consensus",
        ],
        "artifacts": ["predictions.csv", "robot_candidate_comparison.jpg"],
    }
    (OUTPUT / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    render_robot_sheet(rows, samples)
    print(json.dumps(report["metrics"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
