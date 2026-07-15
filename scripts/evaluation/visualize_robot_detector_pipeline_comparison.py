"""Visualize old/new detector routes feeding the same M8 classifier."""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from deskmate_baseline.domain.contracts import FramePacket
from deskmate_baseline.perception.localization import UltralyticsCatLocalizerBackend, route_classification_roi


ROOT = Path(__file__).resolve().parents[2]


def read_bgr(path: Path) -> np.ndarray:
    image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"cannot decode {path}")
    return image


def font(size: int) -> ImageFont.ImageFont:
    path = Path("C:/Windows/Fonts/arial.ttf")
    return ImageFont.truetype(str(path), size) if path.is_file() else ImageFont.load_default()


def contain(image: Image.Image, width: int, height: int) -> Image.Image:
    copy = image.copy()
    copy.thumbnail((width, height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (width, height), "white")
    canvas.paste(copy, ((width - copy.width) // 2, (height - copy.height) // 2))
    return canvas


def route_all(
    model_path: Path,
    manifest: list[dict[str, str]],
    device: str,
    confidence: float,
    padding_ratio: float,
):
    backend = UltralyticsCatLocalizerBackend(
        checkpoint=model_path,
        device=device,
        imgsz=640,
        confidence_threshold=confidence,
        minimum_box_area_ratio=0.02,
        maximum_frame_age_ms=5000,
    )
    backend.load()
    backend.warmup()
    routed = {}
    for frame_id, row in enumerate(manifest):
        path = ROOT / row["selected_relative_path"]
        image = read_bgr(path)
        height, width = image.shape[:2]
        frame = FramePacket(
            frame_id=frame_id,
            captured_at_ns=time.time_ns(),
            image_bgr=image,
            source=str(path),
            width=width,
            height=height,
        )
        observation = backend.infer(frame)
        roi = route_classification_roi(
            frame,
            observation,
            box_is_stable=bool(observation.valid and observation.boxes),
            padding_ratio=padding_ratio,
            fallback_center_scale=0.8,
            minimum_padded_short_side_pixels=32,
        )
        routed[row["sample_id"]] = (observation, roi)
    backend.close()
    return routed


def build_sheet(
    records: list[dict[str, str]],
    old_rows: dict[str, dict[str, str]],
    new_rows: dict[str, dict[str, str]],
    old_routes,
    new_routes,
    output: Path,
) -> None:
    cell_w, cell_h, cols = 780, 270, 3
    if not records:
        sheet = Image.new("RGB", (cell_w, 80), "white")
        ImageDraw.Draw(sheet).text(
            (12, 24), "No samples changed correctness between OLD and NEW.", fill="black", font=font(18)
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(output, quality=92)
        return
    sheet = Image.new("RGB", (cell_w * cols, cell_h * ((len(records) + cols - 1) // cols)), "white")
    title_font, text_font = font(16), font(13)
    for index, record in enumerate(records):
        sample_id = record["sample_id"]
        path = ROOT / record["selected_relative_path"]
        bgr = read_bgr(path)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        original = Image.fromarray(rgb)
        annotated = original.copy()
        draw = ImageDraw.Draw(annotated)
        for label, color, routes in (("O", (0, 220, 0), old_routes), ("N", (0, 180, 255), new_routes)):
            observation, roi = routes[sample_id]
            if roi.mode == "detector_crop":
                x1, y1, x2, y2 = roi.pixel_xyxy
                draw.rectangle((x1, y1, x2, y2), outline=color, width=4)
                draw.text((x1 + 3, y1 + 3), label, fill=color, font=title_font)

        panel = Image.new("RGB", (cell_w, cell_h), "white")
        panel_draw = ImageDraw.Draw(panel)
        panel_draw.text(
            (5, 4),
            f"{path.name} | truth={record['label']} | {record['tier']}",
            fill="black",
            font=title_font,
        )
        panel.paste(contain(annotated, 245, 220), (5, 38))
        panel_draw.text((5, 242), "green=old crop, cyan=new crop", fill="black", font=text_font)

        for left, label, rows, routes in (
            (260, "OLD", old_rows, old_routes),
            (520, "NEW", new_rows, new_routes),
        ):
            observation, roi = routes[sample_id]
            crop_rgb = cv2.cvtColor(roi.image_bgr, cv2.COLOR_BGR2RGB)
            panel.paste(contain(Image.fromarray(crop_rgb), 250, 190), (left, 68))
            row = rows[sample_id]
            prediction = row["route_prediction"]
            correct = row["route_correct"].casefold() == "true"
            color = (0, 145, 0) if correct else (210, 0, 0)
            panel_draw.text(
                (left, 35),
                f"{label}: {prediction} {float(row['route_confidence']):.2f}",
                fill=color,
                font=title_font,
            )
            panel_draw.text(
                (left, 53),
                f"{roi.mode}; boxes={len(observation.boxes)}",
                fill="black",
                font=text_font,
            )
        sheet.paste(panel, ((index % cols) * cell_w, (index // cols) * cell_h))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=92)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--selection", type=Path, default=ROOT / "data/downloads/Camera/model_test_selection_20260715"
    )
    parser.add_argument("--old-detector", type=Path, default=ROOT / "models/yolo26s.pt")
    parser.add_argument(
        "--new-detector",
        type=Path,
        default=ROOT / "runs/detector_tuner/bd02-sphynx-pallas-seed-20260715/weights/best.pt",
    )
    parser.add_argument("--old-csv", default="bm08_detector_classifier_attribution_24.csv")
    parser.add_argument("--new-csv", default="bd02_m08_full_pipeline_24.csv")
    parser.add_argument("--old-confidence", type=float, default=0.25)
    parser.add_argument("--new-confidence", type=float, default=0.25)
    parser.add_argument("--old-padding", type=float, default=0.15)
    parser.add_argument("--new-padding", type=float, default=0.15)
    parser.add_argument("--output-dir", default="bd02_m08_full_pipeline_review")
    parser.add_argument("--device", default="0")
    args = parser.parse_args()
    selection = args.selection.resolve()

    with (selection / "manifest.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        manifest = list(csv.DictReader(handle))
    with (selection / args.old_csv).open("r", encoding="utf-8-sig", newline="") as handle:
        old_rows = {row["sample_id"]: row for row in csv.DictReader(handle)}
    with (selection / args.new_csv).open("r", encoding="utf-8-sig", newline="") as handle:
        new_rows = {row["sample_id"]: row for row in csv.DictReader(handle)}

    old_routes = route_all(
        args.old_detector.resolve(), manifest, args.device, args.old_confidence, args.old_padding
    )
    new_routes = route_all(
        args.new_detector.resolve(), manifest, args.device, args.new_confidence, args.new_padding
    )
    output = selection / args.output_dir
    build_sheet(manifest, old_rows, new_rows, old_routes, new_routes, output / "all_24_old_vs_new.jpg")
    changed = [
        row
        for row in manifest
        if old_rows[row["sample_id"]]["route_correct"] != new_rows[row["sample_id"]]["route_correct"]
    ]
    build_sheet(changed, old_rows, new_rows, old_routes, new_routes, output / "changed_7_old_vs_new.jpg")
    print(f"wrote {len(manifest)}-image and {len(changed)}-transition sheets to {output}")


if __name__ == "__main__":
    main()
