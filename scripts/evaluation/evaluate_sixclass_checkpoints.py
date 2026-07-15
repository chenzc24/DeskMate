from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
LABELS = ("ragdoll", "singapura", "persian", "sphynx", "pallas", "not_target")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_name(value: str) -> str:
    normalized = value.strip().casefold().replace(" ", "_")
    pieces = normalized.split("_", 1)
    return pieces[1] if len(pieces) == 2 and pieces[0].isdigit() else normalized


def parse_checkpoint(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("checkpoint must be NAME=PATH")
    name, raw_path = value.split("=", 1)
    path = Path(raw_path).resolve()
    if not name or not path.is_file():
        raise argparse.ArgumentTypeError(f"invalid checkpoint: {value}")
    return name, path


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    targets = [row for row in rows if row["true_label"] != "not_target"]
    negatives = [row for row in rows if row["true_label"] == "not_target"]
    confusion = {
        true_label: {
            predicted_label: sum(
                row["true_label"] == true_label and row["prediction"] == predicted_label
                for row in rows
            )
            for predicted_label in LABELS
        }
        for true_label in LABELS
    }
    by_class = {}
    for label in LABELS:
        selected = [row for row in rows if row["true_label"] == label]
        correct = sum(row["correct"] for row in selected)
        by_class[label] = {
            "correct": correct,
            "total": len(selected),
            "recall": correct / len(selected) if selected else None,
        }
    return {
        "total": total,
        "correct": sum(row["correct"] for row in rows),
        "accuracy": sum(row["correct"] for row in rows) / total,
        "target_total": len(targets),
        "target_correct": sum(row["correct"] for row in targets),
        "target_accuracy": sum(row["correct"] for row in targets) / len(targets),
        "target_rejected_as_not_target": sum(
            row["prediction"] == "not_target" for row in targets
        ),
        "not_target_total": len(negatives),
        "not_target_rejected": sum(row["correct"] for row in negatives),
        "not_target_rejection": sum(row["correct"] for row in negatives) / len(negatives),
        "not_target_accepted_as_target": sum(not row["correct"] for row in negatives),
        "by_class": by_class,
        "prediction_counts": dict(Counter(row["prediction"] for row in rows)),
        "confusion": confusion,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument(
        "--checkpoint", action="append", type=parse_checkpoint, required=True
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default=0)
    parser.add_argument("--imgsz", type=int, default=224)
    parser.add_argument("--batch", type=int, default=64)
    args = parser.parse_args()
    dataset = args.dataset.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    from ultralytics import YOLO

    all_rows: list[dict[str, Any]] = []
    models: dict[str, Any] = {}
    for model_name, checkpoint in args.checkpoint:
        model = YOLO(str(checkpoint), task="classify")
        native_names = {
            int(index): normalize_name(name) for index, name in model.names.items()
        }
        if set(native_names.values()) != set(LABELS):
            raise ValueError(f"{model_name} is not an exact six-class model: {native_names}")
        models[model_name] = {
            "checkpoint": str(checkpoint),
            "sha256": sha256_file(checkpoint),
        }
        for split in ("val", "val_cal"):
            split_root = dataset / split
            image_paths = sorted(
                str(path.resolve())
                for path in split_root.rglob("*")
                if path.is_file()
                and path.suffix.casefold()
                in {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
            )
            results = model.predict(
                source=image_paths,
                device=args.device,
                imgsz=args.imgsz,
                batch=args.batch,
                verbose=False,
            )
            expected = len(image_paths)
            if len(results) != expected:
                raise RuntimeError(
                    f"{model_name}/{split}: predicted {len(results)} of {expected} files"
                )
            for result, image_path in zip(results, image_paths, strict=True):
                # Ultralytics assigns virtual imageN.jpg names when input is a list;
                # retain the ordered source path for the ground-truth directory.
                path = Path(image_path)
                true_label = normalize_name(path.parent.name)
                probabilities = result.probs.data.detach().float().cpu().numpy()
                predicted_index = int(probabilities.argmax())
                prediction = native_names[predicted_index]
                order = probabilities.argsort()[::-1]
                all_rows.append(
                    {
                        "model": model_name,
                        "split": split,
                        "path": str(path),
                        "true_label": true_label,
                        "prediction": prediction,
                        "confidence": float(probabilities[order[0]]),
                        "margin": float(probabilities[order[0]] - probabilities[order[1]]),
                        "correct": prediction == true_label,
                    }
                )
    report = {
        "schema_version": 1,
        "status": "SIXCLASS_CHECKPOINT_COMPARISON_COMPLETE",
        "dataset": str(dataset),
        "models": models,
        "metrics": {
            model_name: {
                split: summarize(
                    [
                        row
                        for row in all_rows
                        if row["model"] == model_name and row["split"] == split
                    ]
                )
                for split in ("val", "val_cal")
            }
            for model_name, _ in args.checkpoint
        },
        "limitations": [
            "The 65 machine-view images are training samples and are not evaluated as a holdout.",
            "val and val_cal are inherited baseline monitoring/calibration data, not a new robot-camera test set.",
        ],
    }
    csv_path = output / "predictions.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)
    (output / "comparison_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
