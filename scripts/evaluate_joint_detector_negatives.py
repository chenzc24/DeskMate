"""Measure detector false positives on the existing not-target replay set."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from evaluate_joint_detector_tuner import IMAGE_SUFFIXES, accepted, comparison_sheet, predict


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-model", type=Path, default=Path("models/yolo26s.pt"))
    parser.add_argument(
        "--new-model",
        type=Path,
        default=Path("runs/detector_tuner/bd02-sphynx-pallas-seed-20260715/weights/best.pt"),
    )
    parser.add_argument(
        "--replay-data",
        type=Path,
        default=Path("data/downloads/baseline_merged_gapfill_nocat_20260715/one_view_yolo_classify"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/downloads/detector_tuner_sphynx_pallas_evaluation_20260715/negatives"),
    )
    parser.add_argument("--device", default="0")
    parser.add_argument("--confidence", type=float, default=0.25)
    parser.add_argument("--min-area", type=float, default=0.02)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)

    records: list[dict[str, object]] = []
    for split in ("val", "val_cal"):
        directory = args.replay_data / split / "5_not_target"
        for path in sorted(directory.iterdir()):
            if path.suffix.lower() in IMAGE_SUFFIXES:
                records.append({"path": str(path.resolve()), "breed": "not_target", "split": split})
    paths = [Path(str(record["path"])) for record in records]
    old_predictions = predict(
        args.old_model, paths, class_id=15, device=args.device, confidence=args.confidence
    )
    new_predictions = predict(
        args.new_model, paths, class_id=0, device=args.device, confidence=args.confidence
    )

    rows: list[dict[str, object]] = []
    for record in records:
        path = Path(str(record["path"]))
        row: dict[str, object] = {"sample_id": path.stem, "split": record["split"], "path": str(path)}
        for name, predictions in (
            ("old", old_predictions[str(path.resolve())]),
            ("new", new_predictions[str(path.resolve())]),
        ):
            usable = accepted(predictions, args.min_area)
            row[f"{name}_raw_count"] = len(predictions)
            row[f"{name}_accepted_count"] = len(usable)
            row[f"{name}_max_confidence"] = max((box.confidence for box in usable), default=0.0)
        rows.append(row)

    with (args.output / "predictions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    false_positive_records = [
        record for record, row in zip(records, rows, strict=True) if int(row["new_accepted_count"]) > 0
    ]
    if false_positive_records:
        comparison_sheet(
            false_positive_records,
            old_predictions,
            new_predictions,
            args.output / "new_false_positives_old_vs_new.jpg",
            args.min_area,
        )

    report = {
        "images": len(rows),
        "config": {"confidence": args.confidence, "min_area_ratio": args.min_area, "imgsz": 640},
        "old_false_positive_images": sum(int(row["old_accepted_count"]) > 0 for row in rows),
        "new_false_positive_images": sum(int(row["new_accepted_count"]) > 0 for row in rows),
        "old_multi_box_images": sum(int(row["old_accepted_count"]) > 1 for row in rows),
        "new_multi_box_images": sum(int(row["new_accepted_count"]) > 1 for row in rows),
    }
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
