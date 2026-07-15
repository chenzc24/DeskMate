from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from deskmate_baseline.contracts import FramePacket, REPORTABLE_LABELS
from deskmate_baseline.localization import (
    UltralyticsCatLocalizerBackend,
    route_classification_roi,
)


ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_image(path: Path) -> np.ndarray:
    image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"cannot decode image: {path}")
    return image


def normalize_name(value: str) -> str:
    normalized = value.strip().casefold().replace(" ", "_")
    pieces = normalized.split("_", 1)
    return pieces[1] if len(pieces) == 2 and pieces[0].isdigit() else normalized


def model_probabilities(model, image: np.ndarray, device: int | str) -> np.ndarray:
    result = model.predict(source=image, device=device, verbose=False)[0]
    native = result.probs.data.detach().float().cpu().numpy()
    names = {int(index): normalize_name(name) for index, name in result.names.items()}
    if set(names.values()) != set(REPORTABLE_LABELS):
        raise ValueError(f"model is not an exact target-five classifier: {names}")
    return np.asarray(
        [native[next(index for index, name in names.items() if name == label)] for label in REPORTABLE_LABELS],
        dtype=np.float64,
    )


def prediction(probabilities: np.ndarray) -> tuple[str, float, float]:
    order = np.argsort(-probabilities)
    return (
        REPORTABLE_LABELS[int(order[0])],
        float(probabilities[order[0]]),
        float(probabilities[order[0]] - probabilities[order[1]]),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument(
        "--selection",
        type=Path,
        default=ROOT / "data/downloads/Camera/model_test_selection_20260715",
    )
    parser.add_argument("--detector", type=Path, default=ROOT / "models/yolo26s.pt")
    parser.add_argument("--device", default=0)
    parser.add_argument("--output-prefix", default="target5_robot_evaluation")
    parser.add_argument("--route-only", action="store_true")
    parser.add_argument("--detector-imgsz", type=int, default=640)
    parser.add_argument("--detector-confidence", type=float, default=0.25)
    parser.add_argument("--minimum-box-area-ratio", type=float, default=0.02)
    parser.add_argument("--fallback-center-scale", type=float, default=0.8)
    parser.add_argument("--padding-ratio", type=float, default=0.15)
    args = parser.parse_args()
    checkpoint = args.checkpoint.resolve()
    selection = args.selection.resolve()
    detector_path = args.detector.resolve()
    from ultralytics import YOLO

    classifier = YOLO(str(checkpoint), task="classify")
    detector = UltralyticsCatLocalizerBackend(
        checkpoint=detector_path,
        device=args.device,
        imgsz=args.detector_imgsz,
        confidence_threshold=args.detector_confidence,
        minimum_box_area_ratio=args.minimum_box_area_ratio,
        maximum_frame_age_ms=5000,
    )
    detector.load()
    detector.warmup()
    with (selection / "manifest.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        manifest = list(csv.DictReader(handle))
    rows: list[dict[str, object]] = []
    modes = (
        ("route",)
        if args.route_only
        else (
            "route",
            "full_fallback",
            "full",
            "center",
            "mean_unique",
            "route_weighted",
        )
    )
    for frame_id, source in enumerate(manifest):
        image_path = ROOT / source["selected_relative_path"]
        image = read_image(image_path)
        height, width = image.shape[:2]
        frame = FramePacket(
            frame_id=frame_id,
            captured_at_ns=time.time_ns(),
            image_bgr=image,
            source=str(image_path),
            width=width,
            height=height,
        )
        observation = detector.infer(frame)
        routed = route_classification_roi(
            frame,
            observation,
            box_is_stable=bool(observation.valid and observation.boxes),
            padding_ratio=args.padding_ratio,
            fallback_center_scale=args.fallback_center_scale,
            minimum_padded_short_side_pixels=32,
        )
        route_p = model_probabilities(classifier, routed.image_bgr, args.device)
        if args.route_only:
            probabilities = {"route": route_p}
        else:
            roi_height = int(round(height * 0.8))
            roi_width = int(round(width * 0.8))
            top = (height - roi_height) // 2
            left = (width - roi_width) // 2
            center = image[top : top + roi_height, left : left + roi_width]
            full_p = model_probabilities(classifier, image, args.device)
            center_p = model_probabilities(classifier, center, args.device)
            if routed.mode == "detector_crop":
                mean_p = (route_p + full_p + center_p) / 3.0
                weighted_p = route_p * 0.6 + center_p * 0.2 + full_p * 0.2
            else:
                mean_p = (full_p + center_p) / 2.0
                weighted_p = center_p * 0.7 + full_p * 0.3
            probabilities = {
                "route": route_p,
                "full_fallback": (
                    route_p if routed.mode == "detector_crop" else full_p
                ),
                "full": full_p,
                "center": center_p,
                "mean_unique": mean_p,
                "route_weighted": weighted_p,
            }
        row: dict[str, object] = {
            "sample_id": source["sample_id"],
            "filename": image_path.name,
            "true_label": source["label"],
            "tier": source["tier"],
            "source_group_id": source["source_group_id"],
            "route_mode": routed.mode,
            "route_reason": routed.route_reason,
            "detector_box_count": len(observation.boxes),
        }
        for mode in modes:
            label, confidence, margin = prediction(probabilities[mode])
            row[f"{mode}_prediction"] = label
            row[f"{mode}_confidence"] = confidence
            row[f"{mode}_margin"] = margin
            row[f"{mode}_correct"] = label == source["label"]
        rows.append(row)
    summary: dict[str, object] = {}
    for mode in modes:
        correct = sum(bool(row[f"{mode}_correct"]) for row in rows)
        summary[mode] = {
            "correct": correct,
            "total": len(rows),
            "accuracy_descriptive": correct / len(rows),
            "by_class": {
                label: {
                    "correct": sum(
                        bool(row[f"{mode}_correct"])
                        for row in rows
                        if row["true_label"] == label
                    ),
                    "total": sum(row["true_label"] == label for row in rows),
                }
                for label in REPORTABLE_LABELS
            },
        }
    group_rows = []
    for group_id in sorted({str(row["source_group_id"]) for row in rows}):
        selected = [row for row in rows if row["source_group_id"] == group_id]
        votes = Counter(str(row["route_prediction"]) for row in selected)
        confidence_sums = {
            label: sum(
                float(row["route_confidence"])
                for row in selected
                if row["route_prediction"] == label
            )
            for label in REPORTABLE_LABELS
        }
        predicted = max(
            REPORTABLE_LABELS,
            key=lambda label: (votes[label], confidence_sums[label]),
        )
        truth = str(selected[0]["true_label"])
        group_rows.append(
            {
                "source_group_id": group_id,
                "true_label": truth,
                "prediction": predicted,
                "correct": predicted == truth,
                "frame_count": len(selected),
            }
        )
    group_correct = sum(bool(row["correct"]) for row in group_rows)
    report = {
        "schema_version": 1,
        "status": "TARGET5_ROBOT_DIAGNOSTIC_COMPLETE",
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": sha256_file(checkpoint),
        "detector": str(detector_path),
        "detector_sha256": sha256_file(detector_path),
        "detector_parameters": {
            "imgsz": args.detector_imgsz,
            "confidence_threshold": args.detector_confidence,
            "minimum_box_area_ratio": args.minimum_box_area_ratio,
            "fallback_center_scale": args.fallback_center_scale,
            "padding_ratio": args.padding_ratio,
        },
        "selection_count": len(rows),
        "selection_manifest_sha256": sha256_file(selection / "manifest.csv"),
        "summary": summary,
        "source_group_summary": {
            "aggregation": "majority_vote_then_summed_confidence_tiebreak",
            "correct": group_correct,
            "total": len(group_rows),
            "accuracy_descriptive": group_correct / len(group_rows),
            "groups": group_rows,
        },
        "limitations": [
            "target-only diagnostic set cannot measure rejection",
            "correlated burst frames are not a final independent holdout",
            "fusion policy comparison uses this set as development data",
        ],
    }
    csv_path = selection / f"{args.output_prefix}.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (selection / f"{args.output_prefix}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
