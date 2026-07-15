"""Compare the baseline and tuned cat detectors on held-out and replay images."""

from __future__ import annotations

import argparse
import csv
import gc
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import torch
from PIL import Image, ImageDraw, ImageFont, ImageOps
from ultralytics import YOLO


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass
class Box:
    xyxy: tuple[float, float, float, float]
    confidence: float
    area_ratio: float


def parse_yolo(path: Path, width: int, height: int) -> list[tuple[float, float, float, float]]:
    boxes = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        class_id, x, y, w, h = raw.split()
        if int(class_id) != 0:
            raise ValueError(f"unexpected class in {path}")
        x, y, w, h = (float(value) for value in (x, y, w, h))
        boxes.append(((x - w / 2) * width, (y - h / 2) * height, (x + w / 2) * width, (y + h / 2) * height))
    return boxes


def iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    intersection = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    union = area_a + area_b - intersection
    return intersection / union if union else 0.0


def predict(
    model_path: Path,
    paths: list[Path],
    class_id: int,
    device: str,
    confidence: float = 0.25,
) -> dict[str, list[Box]]:
    model = YOLO(str(model_path.resolve()))
    predictions: dict[str, list[Box]] = {}
    results = model.predict(
        source=[str(path.resolve()) for path in paths],
        imgsz=640,
        conf=confidence,
        iou=0.7,
        classes=[class_id],
        device=device,
        stream=True,
        verbose=False,
    )
    for path, result in zip(paths, results, strict=True):
        height, width = result.orig_shape
        image_area = float(width * height)
        boxes: list[Box] = []
        if result.boxes is not None:
            for xyxy, confidence in zip(result.boxes.xyxy.cpu().tolist(), result.boxes.conf.cpu().tolist(), strict=True):
                x1, y1, x2, y2 = (float(value) for value in xyxy)
                area_ratio = max(0.0, x2 - x1) * max(0.0, y2 - y1) / image_area
                boxes.append(Box((x1, y1, x2, y2), float(confidence), area_ratio))
        predictions[str(path.resolve())] = boxes
    del model
    gc.collect()
    torch.cuda.empty_cache()
    return predictions


def accepted(boxes: list[Box], min_area: float) -> list[Box]:
    return [box for box in boxes if box.area_ratio >= min_area]


def summarize_test(rows: list[dict[str, object]], model_name: str) -> dict[str, object]:
    summary: dict[str, object] = {}
    for breed in ("sphynx", "pallas", "all"):
        selected = rows if breed == "all" else [row for row in rows if row["breed"] == breed]
        gt_count = sum(int(row["gt_count"]) for row in selected)
        summary[breed] = {
            "images": len(selected),
            "raw_detection_images": sum(int(row[f"{model_name}_raw_count"]) > 0 for row in selected),
            "accepted_detection_images": sum(int(row[f"{model_name}_accepted_count"]) > 0 for row in selected),
            "matched_images_iou50": sum(bool(row[f"{model_name}_matched_image_iou50"]) for row in selected),
            "gt_boxes": gt_count,
            "gt_recall_iou50": (
                sum(int(row[f"{model_name}_matched_gt_iou50"]) for row in selected) / gt_count if gt_count else 0.0
            ),
            "mean_best_gt_iou": (
                sum(float(row[f"{model_name}_best_iou_sum"]) for row in selected) / gt_count if gt_count else 0.0
            ),
            "multi_accepted_images": sum(int(row[f"{model_name}_accepted_count"]) > 1 for row in selected),
        }
    return summary


def summarize_replay(rows: list[dict[str, object]], model_name: str) -> dict[str, object]:
    summary: dict[str, object] = {}
    breeds = sorted({str(row["breed"]) for row in rows})
    for breed in breeds + ["all"]:
        selected = rows if breed == "all" else [row for row in rows if row["breed"] == breed]
        summary[breed] = {
            "images": len(selected),
            "raw_detection_images": sum(int(row[f"{model_name}_raw_count"]) > 0 for row in selected),
            "accepted_detection_images": sum(int(row[f"{model_name}_accepted_count"]) > 0 for row in selected),
            "multi_accepted_images": sum(int(row[f"{model_name}_accepted_count"]) > 1 for row in selected),
            "mean_max_confidence": (
                sum(float(row[f"{model_name}_max_confidence"]) for row in selected) / len(selected) if selected else 0.0
            ),
        }
    return summary


def draw_boxes(image: Image.Image, boxes: list[Box], min_area: float) -> Image.Image:
    rendered = image.copy()
    draw = ImageDraw.Draw(rendered)
    for box in boxes:
        if box.area_ratio < min_area:
            continue
        x1, y1, x2, y2 = box.xyxy
        draw.rectangle((x1, y1, x2, y2), outline=(0, 230, 0), width=max(3, image.width // 250))
        draw.text((x1 + 3, y1 + 3), f"{box.confidence:.2f}", fill=(0, 255, 0))
    return rendered


def comparison_sheet(
    records: list[dict[str, object]],
    old_predictions: dict[str, list[Box]],
    new_predictions: dict[str, list[Box]],
    output: Path,
    min_area: float,
) -> None:
    cols, cell_w, cell_h = 4, 600, 280
    sheet = Image.new("RGB", (cols * cell_w, math.ceil(len(records) / cols) * cell_h), "white")
    font = ImageFont.load_default()
    for index, record in enumerate(records):
        path = Path(str(record["path"]))
        with Image.open(path) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
        panel = Image.new("RGB", (cell_w, cell_h), "white")
        draw = ImageDraw.Draw(panel)
        title = f"{record['breed']} | {path.stem}"
        draw.text((5, 4), title, fill="black", font=font)
        for offset, label, predictions in (
            (5, "OLD", old_predictions[str(path.resolve())]),
            (305, "NEW", new_predictions[str(path.resolve())]),
        ):
            rendered = draw_boxes(image, predictions, min_area)
            rendered.thumbnail((286, 235), Image.Resampling.LANCZOS)
            panel.paste(rendered, (offset, 34))
            count = len(accepted(predictions, min_area))
            color = (0, 150, 0) if count else (220, 0, 0)
            draw.text((offset, 20), f"{label}: {count} accepted", fill=color, font=font)
        sheet.paste(panel, ((index % cols) * cell_w, (index // cols) * cell_h))
    sheet.save(output, quality=92)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-model", type=Path, default=Path("models/yolo26s.pt"))
    parser.add_argument(
        "--new-model",
        type=Path,
        default=Path("runs/detector_tuner/bd02-sphynx-pallas-seed-20260715/weights/best.pt"),
    )
    parser.add_argument(
        "--joint-data",
        type=Path,
        default=Path("data/downloads/detector_tuner_sphynx_pallas_yolo_20260715"),
    )
    parser.add_argument(
        "--replay-data",
        type=Path,
        default=Path("data/downloads/baseline_merged_gapfill_nocat_20260715/one_view_yolo_classify"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/downloads/detector_tuner_sphynx_pallas_evaluation_20260715"),
    )
    parser.add_argument("--device", default="0")
    parser.add_argument("--min-area", type=float, default=0.02)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)

    test_records: list[dict[str, object]] = []
    for breed in ("sphynx", "pallas"):
        prefix = "target-sphynx" if breed == "sphynx" else "Pallas_cat"
        for path in sorted((args.joint_data / "images" / "test").iterdir()):
            if path.suffix.lower() in IMAGE_SUFFIXES and path.stem.startswith(prefix):
                test_records.append({"path": str(path.resolve()), "breed": breed})

    replay_records: list[dict[str, object]] = []
    for split in ("val", "val_cal"):
        for breed_dir in sorted((args.replay_data / split).iterdir()):
            if not breed_dir.is_dir() or breed_dir.name.startswith("5_"):
                continue
            breed = breed_dir.name.split("_", 1)[1]
            for path in sorted(breed_dir.iterdir()):
                if path.suffix.lower() in IMAGE_SUFFIXES:
                    replay_records.append({"path": str(path.resolve()), "breed": breed, "split": split})

    all_paths = [Path(str(record["path"])) for record in test_records + replay_records]
    old_predictions = predict(args.old_model, all_paths, class_id=15, device=args.device)
    new_predictions = predict(args.new_model, all_paths, class_id=0, device=args.device)

    test_rows: list[dict[str, object]] = []
    for record in test_records:
        image_path = Path(str(record["path"]))
        with Image.open(image_path) as image:
            width, height = image.size
        label_path = args.joint_data / "labels" / "test" / f"{image_path.stem}.txt"
        gt = parse_yolo(label_path, width, height)
        row: dict[str, object] = {
            "sample_id": image_path.stem,
            "breed": record["breed"],
            "path": str(image_path),
            "gt_count": len(gt),
        }
        for model_name, predictions in (("old", old_predictions[str(image_path.resolve())]), ("new", new_predictions[str(image_path.resolve())])):
            usable = accepted(predictions, args.min_area)
            best_ious = [max((iou(target, box.xyxy) for box in usable), default=0.0) for target in gt]
            row.update(
                {
                    f"{model_name}_raw_count": len(predictions),
                    f"{model_name}_accepted_count": len(usable),
                    f"{model_name}_max_confidence": max((box.confidence for box in usable), default=0.0),
                    f"{model_name}_matched_gt_iou50": sum(value >= 0.5 for value in best_ious),
                    f"{model_name}_matched_image_iou50": any(value >= 0.5 for value in best_ious),
                    f"{model_name}_best_iou_sum": sum(best_ious),
                }
            )
        test_rows.append(row)

    replay_rows: list[dict[str, object]] = []
    for record in replay_records:
        image_path = Path(str(record["path"]))
        row = {
            "sample_id": image_path.stem,
            "breed": record["breed"],
            "split": record["split"],
            "path": str(image_path),
        }
        for model_name, predictions in (("old", old_predictions[str(image_path.resolve())]), ("new", new_predictions[str(image_path.resolve())])):
            usable = accepted(predictions, args.min_area)
            row.update(
                {
                    f"{model_name}_raw_count": len(predictions),
                    f"{model_name}_accepted_count": len(usable),
                    f"{model_name}_max_confidence": max((box.confidence for box in usable), default=0.0),
                }
            )
        replay_rows.append(row)

    write_csv(args.output / "test_predictions.csv", test_rows)
    write_csv(args.output / "replay_predictions.csv", replay_rows)
    comparison_sheet(
        [record for record in test_records if record["breed"] == "sphynx"],
        old_predictions,
        new_predictions,
        args.output / "test_sphynx_old_vs_new.jpg",
        args.min_area,
    )
    comparison_sheet(
        [record for record in test_records if record["breed"] == "pallas"],
        old_predictions,
        new_predictions,
        args.output / "test_pallas_old_vs_new.jpg",
        args.min_area,
    )
    recovered = [
        record
        for record, row in zip(replay_records, replay_rows, strict=True)
        if int(row["old_accepted_count"]) == 0 and int(row["new_accepted_count"]) > 0
    ][:32]
    if recovered:
        comparison_sheet(
            recovered,
            old_predictions,
            new_predictions,
            args.output / "replay_recovered_old_vs_new.jpg",
            args.min_area,
        )

    report = {
        "config": {"confidence": 0.25, "min_area_ratio": args.min_area, "imgsz": 640, "iou_match": 0.5},
        "models": {"old": str(args.old_model.resolve()), "new": str(args.new_model.resolve())},
        "held_out_test": {
            "old": summarize_test(test_rows, "old"),
            "new": summarize_test(test_rows, "new"),
        },
        "five_breed_replay": {
            "note": "diagnostic presence scan on detector-derived classifier views; no ground-truth boxes",
            "old": summarize_replay(replay_rows, "old"),
            "new": summarize_replay(replay_rows, "new"),
        },
        "transitions": {
            "replay_recovered": sum(
                int(row["old_accepted_count"]) == 0 and int(row["new_accepted_count"]) > 0 for row in replay_rows
            ),
            "replay_regressed": sum(
                int(row["old_accepted_count"]) > 0 and int(row["new_accepted_count"]) == 0 for row in replay_rows
            ),
        },
    }
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
