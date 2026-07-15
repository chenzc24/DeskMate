#!/usr/bin/env python3
"""Compare frozen and hardened detector-to-classifier ROI policies."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
import ultralytics


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from deskmate_baseline.contracts import FramePacket  # noqa: E402
from deskmate_baseline.inference import UltralyticsClassificationBackend  # noqa: E402
from deskmate_baseline.localization import (  # noqa: E402
    LocalizerBox,
    LocalizerObservation,
    UltralyticsCatLocalizerBackend,
    deduplicate_overlapping_boxes,
    route_classification_roi,
)


DETECTOR = ROOT / "models" / "yolo26s.pt"
CLASSIFIER = (
    ROOT
    / "runs"
    / "baseline_provisional"
    / "b-m01-provisional-bd01-oneview-seed-20260715"
    / "weights"
    / "best.pt"
)
EXPECTED_DETECTOR_SHA256 = (
    "646f8bc3fe0a656803d95c294f7852321748cb29d13466a1af8862e2db384a1b"
)
EXPECTED_CLASSIFIER_SHA256 = (
    "c41cfd4a12411883df52bf8643b20a2621b189bbd27c642bae441e92cf06319d"
)
OUTPUT = ROOT / "data" / "downloads" / "baseline_routing_ablation"
SOURCE_ROOTS = (
    ROOT / "data" / "downloads" / "cat_processed",
    ROOT / "data" / "downloads" / "phase1_candidates",
    ROOT / "data" / "downloads" / "baseline_provisional_split",
)
CAMERA_LABELS = (
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


@dataclass(frozen=True)
class Sample:
    group: str
    sample_id: str
    label: str
    path: Path
    frozen_prediction: str | None


@dataclass(frozen=True)
class Policy:
    name: str
    minimum_area_ratio: float
    minimum_short_side_pixels: int
    deduplication_iou: float | None


POLICIES = (
    Policy("control_area002", 0.02, 0, None),
    Policy("area001_only", 0.01, 0, None),
    Policy("pixel64_only", 0.02, 64, None),
    Policy("hardened", 0.01, 64, 0.85),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil(quantile * len(ordered)) - 1)
    return ordered[index]


def resolve_source(relative: str) -> Path:
    matches = [root / relative for root in SOURCE_ROOTS if (root / relative).is_file()]
    if len(matches) != 1:
        raise FileNotFoundError(f"expected one source for {relative!r}; found {matches}")
    return matches[0]


def load_csv_samples(path: Path, group: str) -> list[Sample]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [
        Sample(
            group=group,
            sample_id=row["parent_image_id"],
            label=row["label"],
            path=resolve_source(row["source_relative_path"]),
            frozen_prediction=row.get("prediction") or None,
        )
        for row in rows
    ]


def load_samples() -> list[Sample]:
    samples = load_csv_samples(
        ROOT / "data" / "downloads" / "baseline_full_pipeline_review" / "predictions.csv",
        "biased_40",
    )
    samples.extend(
        load_csv_samples(
            ROOT
            / "data"
            / "downloads"
            / "baseline_full_pipeline_expanded"
            / "predictions.csv",
            "expanded_600",
        )
    )
    camera_paths = sorted((ROOT / "data" / "downloads" / "Camera").glob("*"))
    if len(camera_paths) != len(CAMERA_LABELS):
        raise RuntimeError(
            f"robot camera snapshot changed: expected {len(CAMERA_LABELS)}, got {len(camera_paths)}"
        )
    samples.extend(
        Sample("robot_9", f"robot-{index:02d}", label, path, None)
        for index, (path, label) in enumerate(zip(camera_paths, CAMERA_LABELS), 1)
    )
    return samples


def filtered_boxes(boxes: tuple[LocalizerBox, ...], policy: Policy) -> tuple[LocalizerBox, ...]:
    selected = tuple(box for box in boxes if box.area_ratio >= policy.minimum_area_ratio)
    if policy.deduplication_iou is not None:
        selected = deduplicate_overlapping_boxes(
            selected, iou_threshold=policy.deduplication_iou
        )
    return selected[:5]


def observation_with_boxes(
    observation: LocalizerObservation, boxes: tuple[LocalizerBox, ...]
) -> LocalizerObservation:
    return LocalizerObservation(
        task=observation.task,
        boxes=boxes,
        model_id=observation.model_id,
        frame_id=observation.frame_id,
        captured_at_ns=observation.captured_at_ns,
        inferred_at_ns=observation.inferred_at_ns,
        valid=observation.valid,
        reason=observation.reason,
    )


def classify_roi(
    classifier: UltralyticsClassificationBackend,
    image: np.ndarray,
    *,
    frame_id: int,
) -> tuple[Any, float]:
    started = time.perf_counter_ns()
    packet = FramePacket(
        frame_id=frame_id,
        captured_at_ns=time.time_ns(),
        image_bgr=image,
        source="routing_ablation_roi",
        width=int(image.shape[1]),
        height=int(image.shape[0]),
    )
    result = classifier.infer(packet, "wide")
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    if not result.valid:
        raise RuntimeError(result.reason)
    return result, elapsed_ms


def format_top3(observation: Any) -> str:
    return "|".join(f"{label}:{probability:.8f}" for label, probability in observation.topk)


def render_camera_sheet(rows: list[dict[str, Any]], samples: list[Sample], output: Path) -> None:
    row_by_key = {(row["sample_id"], row["policy"]): row for row in rows}
    tiles: list[np.ndarray] = []
    for sample in (item for item in samples if item.group == "robot_9"):
        image = cv2.imread(str(sample.path), cv2.IMREAD_COLOR)
        canvas = cv2.resize(image, (480, 360), interpolation=cv2.INTER_AREA)
        footer = np.full((120, 480, 3), 245, dtype=np.uint8)
        control = row_by_key[(sample.sample_id, "control_area002")]
        hardened = row_by_key[(sample.sample_id, "hardened")]
        lines = (
            f"GT (visible print): {sample.label}",
            f"CONTROL {control['route']} -> {control['prediction']} {control['confidence']:.3f}",
            f"HARDEN  {hardened['route']} -> {hardened['prediction']} {hardened['confidence']:.3f}",
            f"reason={hardened['route_reason']}",
        )
        for index, line in enumerate(lines):
            cv2.putText(
                footer,
                line,
                (8, 25 + index * 27),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                (20, 20, 20),
                1,
                cv2.LINE_AA,
            )
        tiles.append(np.vstack((canvas, footer)))
    rows_of_tiles = []
    blank = np.full_like(tiles[0], 255)
    for start in range(0, len(tiles), 3):
        chunk = tiles[start : start + 3]
        rows_of_tiles.append(np.hstack(chunk + [blank] * (3 - len(chunk))))
    cv2.imwrite(str(output), np.vstack(rows_of_tiles))


def metric_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    groups = sorted({row["group"] for row in rows})
    policies = [policy.name for policy in POLICIES]
    for group in groups:
        group_rows = [row for row in rows if row["group"] == group]
        summary[group] = {}
        control = {
            row["sample_id"]: row
            for row in group_rows
            if row["policy"] == "control_area002"
        }
        for policy in policies:
            selected = [row for row in group_rows if row["policy"] == policy]
            correct = sum(bool(row["correct"]) for row in selected)
            changed = [
                row
                for row in selected
                if row["prediction"] != control[row["sample_id"]]["prediction"]
                or row["route"] != control[row["sample_id"]]["route"]
            ]
            corrections = sum(
                bool(row["correct"])
                and not bool(control[row["sample_id"]]["correct"])
                for row in selected
            )
            regressions = sum(
                not bool(row["correct"])
                and bool(control[row["sample_id"]]["correct"])
                for row in selected
            )
            summary[group][policy] = {
                "count": len(selected),
                "correct": correct,
                "descriptive_accuracy": correct / len(selected),
                "route_counts": dict(Counter(row["route"] for row in selected)),
                "route_reason_counts": dict(
                    Counter(row["route_reason"] for row in selected)
                ),
                "changed_from_control": len(changed),
                "corrections_from_control": corrections,
                "regressions_from_control": regressions,
            }
    return summary


def main() -> int:
    if sha256_file(DETECTOR) != EXPECTED_DETECTOR_SHA256:
        raise RuntimeError("detector checksum mismatch")
    if sha256_file(CLASSIFIER) != EXPECTED_CLASSIFIER_SHA256:
        raise RuntimeError("classifier checksum mismatch")
    samples = load_samples()
    OUTPUT.mkdir(parents=True, exist_ok=True)

    detector = UltralyticsCatLocalizerBackend(
        checkpoint=DETECTOR,
        device=0,
        imgsz=640,
        confidence_threshold=0.25,
        minimum_box_area_ratio=0.0,
        maximum_candidates=20,
        candidate_deduplication_iou_threshold=1.0,
        maximum_frame_age_ms=60_000.0,
    )
    classifier = UltralyticsClassificationBackend(
        checkpoint=CLASSIFIER,
        device=0,
        imgsz=224,
        temperature=1.0,
        maximum_frame_age_ms=60_000.0,
    )
    detector.load()
    classifier.load()
    detector.warmup()
    classifier.warmup()

    rows: list[dict[str, Any]] = []
    low_confidence_robot_rows: list[dict[str, Any]] = []
    detector_latencies: list[float] = []
    classifier_latencies: list[float] = []
    next_frame_id = 1
    try:
        for sample in samples:
            image = cv2.imread(str(sample.path), cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError(f"could not decode {sample.path}")
            frame = FramePacket(
                frame_id=next_frame_id,
                captured_at_ns=time.time_ns(),
                image_bgr=image,
                source=str(sample.path.relative_to(ROOT)),
                width=int(image.shape[1]),
                height=int(image.shape[0]),
            )
            next_frame_id += 1
            started = time.perf_counter_ns()
            raw_observation = detector.infer(frame)
            detector_ms = (time.perf_counter_ns() - started) / 1_000_000
            detector_latencies.append(detector_ms)
            if not raw_observation.valid:
                raise RuntimeError(raw_observation.reason)
            prediction_cache: dict[tuple[int, int, int, int], tuple[Any, float]] = {}
            for policy in POLICIES:
                boxes = filtered_boxes(raw_observation.boxes, policy)
                routed = route_classification_roi(
                    frame,
                    observation_with_boxes(raw_observation, boxes),
                    box_is_stable=True,
                    padding_ratio=0.15,
                    fallback_center_scale=0.8,
                    minimum_padded_short_side_pixels=policy.minimum_short_side_pixels,
                )
                if routed.pixel_xyxy not in prediction_cache:
                    result, classifier_ms = classify_roi(
                        classifier, routed.image_bgr, frame_id=next_frame_id
                    )
                    next_frame_id += 1
                    prediction_cache[routed.pixel_xyxy] = (result, classifier_ms)
                    classifier_latencies.append(classifier_ms)
                result, classifier_ms = prediction_cache[routed.pixel_xyxy]
                rows.append(
                    {
                        "group": sample.group,
                        "sample_id": sample.sample_id,
                        "label": sample.label,
                        "source_relative_path": str(sample.path.relative_to(ROOT)),
                        "policy": policy.name,
                        "raw_box_count_conf025": len(raw_observation.boxes),
                        "policy_box_count": len(boxes),
                        "route": routed.mode,
                        "route_reason": routed.route_reason,
                        "selected_detector_confidence": (
                            boxes[0].confidence if boxes and routed.mode == "detector_crop" else None
                        ),
                        "roi_xyxy_pixels": "|".join(map(str, routed.pixel_xyxy)),
                        "prediction": result.label,
                        "confidence": result.calibrated_confidence,
                        "margin": result.margin,
                        "top3": format_top3(result),
                        "correct": result.label == sample.label,
                        "detector_ms_shared": detector_ms,
                        "classifier_ms_cached": classifier_ms,
                    }
                )

        low_confidence_detector = UltralyticsCatLocalizerBackend(
            checkpoint=DETECTOR,
            device=0,
            imgsz=640,
            confidence_threshold=0.01,
            minimum_box_area_ratio=0.0,
            maximum_candidates=20,
            candidate_deduplication_iou_threshold=0.85,
            maximum_frame_age_ms=60_000.0,
        )
        low_confidence_detector.load()
        low_confidence_detector.warmup()
        try:
            for sample in (item for item in samples if item.group == "robot_9"):
                image = cv2.imread(str(sample.path), cv2.IMREAD_COLOR)
                frame = FramePacket(
                    frame_id=next_frame_id,
                    captured_at_ns=time.time_ns(),
                    image_bgr=image,
                    source=str(sample.path.relative_to(ROOT)),
                    width=int(image.shape[1]),
                    height=int(image.shape[0]),
                )
                next_frame_id += 1
                observation = low_confidence_detector.infer(frame)
                if not observation.valid:
                    raise RuntimeError(observation.reason)
                candidates = tuple(
                    box for box in observation.boxes if box.confidence < 0.25
                )
                for candidate_index, box in enumerate(candidates, 1):
                    routed = route_classification_roi(
                        frame,
                        observation_with_boxes(observation, (box,)),
                        box_is_stable=True,
                        padding_ratio=0.15,
                        fallback_center_scale=0.8,
                        minimum_padded_short_side_pixels=64,
                    )
                    result, classifier_ms = classify_roi(
                        classifier, routed.image_bgr, frame_id=next_frame_id
                    )
                    next_frame_id += 1
                    classifier_latencies.append(classifier_ms)
                    low_confidence_robot_rows.append(
                        {
                            "sample_id": sample.sample_id,
                            "label": sample.label,
                            "candidate_index": candidate_index,
                            "detector_confidence": box.confidence,
                            "detector_area_ratio": box.area_ratio,
                            "route": routed.mode,
                            "roi_xyxy_pixels": "|".join(map(str, routed.pixel_xyxy)),
                            "prediction": result.label,
                            "confidence": result.calibrated_confidence,
                            "correct": result.label == sample.label,
                        }
                    )
        finally:
            low_confidence_detector.close()
    finally:
        detector.close()
        classifier.close()

    fieldnames = list(rows[0])
    with (OUTPUT / "predictions.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    if low_confidence_robot_rows:
        with (OUTPUT / "robot_low_confidence_candidates.csv").open(
            "w", encoding="utf-8-sig", newline=""
        ) as handle:
            writer = csv.DictWriter(
                handle, fieldnames=list(low_confidence_robot_rows[0])
            )
            writer.writeheader()
            writer.writerows(low_confidence_robot_rows)

    frozen_rows = [
        row
        for row in rows
        if row["policy"] == "control_area002" and row["group"] != "robot_9"
    ]
    sample_lookup = {sample.sample_id: sample for sample in samples}
    frozen_reproduction_mismatches = [
        row["sample_id"]
        for row in frozen_rows
        if sample_lookup[row["sample_id"]].frozen_prediction != row["prediction"]
    ]
    rows_by_sample = defaultdict(dict)
    for row in rows:
        rows_by_sample[row["sample_id"]][row["policy"]] = row
    deduplicated_samples = [
        sample_id
        for sample_id, policy_rows in rows_by_sample.items()
        if int(policy_rows["hardened"]["policy_box_count"])
        < int(policy_rows["area001_only"]["policy_box_count"])
    ]
    report = {
        "schema_version": 1,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "ROUTING_ABLATION_COMPLETE",
        "sample_roles": {
            "biased_40": "same_deliberately_biased_40_not_release_accuracy",
            "expanded_600": "balanced_diagnostic_contains_training_and_validation_images",
            "robot_9": "visible_printed_labels_no_frozen_ground_truth_manifest",
        },
        "policies": [asdict(policy) for policy in POLICIES],
        "metrics": metric_summary(rows),
        "control_reproduction": {
            "compared_count": len(frozen_rows),
            "prediction_mismatch_count": len(frozen_reproduction_mismatches),
            "mismatch_sample_ids": frozen_reproduction_mismatches,
        },
        "candidate_deduplication": {
            "samples_with_removed_near_duplicate": len(deduplicated_samples),
            "sample_ids": deduplicated_samples,
            "route_or_prediction_changes": sum(
                rows_by_sample[sample_id]["hardened"]["route"]
                != rows_by_sample[sample_id]["area001_only"]["route"]
                or rows_by_sample[sample_id]["hardened"]["prediction"]
                != rows_by_sample[sample_id]["area001_only"]["prediction"]
                for sample_id in deduplicated_samples
            ),
        },
        "robot_low_confidence_diagnostic": {
            "detector_confidence_range": "[0.01, 0.25)",
            "global_threshold_adopted": False,
            "candidate_count": len(low_confidence_robot_rows),
            "correct_candidate_classifications": sum(
                bool(row["correct"]) for row in low_confidence_robot_rows
            ),
            "pallas_candidate_count": sum(
                row["label"] == "pallas" for row in low_confidence_robot_rows
            ),
            "pallas_correct_candidate_classifications": sum(
                row["label"] == "pallas" and bool(row["correct"])
                for row in low_confidence_robot_rows
            ),
            "rows": low_confidence_robot_rows,
        },
        "latency_ms": {
            "detector_shared_mean": statistics.fmean(detector_latencies),
            "detector_shared_p95": percentile(detector_latencies, 0.95),
            "unique_classifier_call_count": len(classifier_latencies),
            "classifier_mean": statistics.fmean(classifier_latencies),
            "classifier_p95": percentile(classifier_latencies, 0.95),
            "note": "policy outputs reused identical ROI classifications; not end-to-end camera timing",
        },
        "models": {
            "detector_sha256": EXPECTED_DETECTOR_SHA256,
            "classifier_sha256": EXPECTED_CLASSIFIER_SHA256,
        },
        "environment": {
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "unavailable",
            "torch": torch.__version__,
            "ultralytics": ultralytics.__version__,
        },
        "limitations": [
            "no_unseen_release_accuracy_claim",
            "robot_labels_are_visible_printed_labels_not_frozen_manifest",
            "static_images_do_not_validate_temporal_consensus",
            "raw_classifier_probabilities_are_uncalibrated",
            "routing_cannot_repair_classifier_domain_errors",
        ],
        "artifacts": [
            "predictions.csv",
            "robot_low_confidence_candidates.csv",
            "robot_control_vs_hardened.jpg",
        ],
    }
    with (OUTPUT / "report.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    render_camera_sheet(rows, samples, OUTPUT / "robot_control_vs_hardened.jpg")
    print(json.dumps(report["metrics"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
