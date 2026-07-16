"""Build automatic screen/print domain augmentation for the cat detector.

Existing YOLO boxes are propagated through a perspective homography, so the
generated positives require no new manual annotation. Blank framed composites
are generated as hard negatives to prevent learning "rectangle means cat".
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def materialize_tree(source: Path, output: Path) -> None:
    """Create a disposable view, hard-linking large training files if possible."""

    output.mkdir(parents=True)
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        target = output / relative
        if path.is_dir():
            target.mkdir(exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix.lower() in IMAGE_SUFFIXES or path.suffix.lower() == ".txt":
            try:
                os.link(path, target)
                continue
            except OSError:
                pass
        shutil.copy2(path, target)


def manifest_file(dataset: Path, row: dict[str, str], kind: str) -> Path:
    """Resolve a row's output file without trusting stale copied paths."""

    suffix = Path(row[f"output_{kind}"]).suffix
    if kind == "image":
        matches = [
            path
            for path in (dataset / "images" / row["split"]).glob(f"{row['sample_id']}.*")
            if path.suffix.lower() in IMAGE_SUFFIXES
        ]
        if len(matches) != 1:
            raise ValueError(f"expected one image for {row['sample_id']}, found {matches}")
        return matches[0]
    return dataset / "labels" / row["split"] / f"{row['sample_id']}{suffix or '.txt'}"


def project_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def read_bgr(path: Path) -> np.ndarray:
    image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"cannot decode image: {path}")
    return image


def write_jpeg(path: Path, image: np.ndarray, quality: int) -> None:
    ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise ValueError(f"cannot encode image: {path}")
    encoded.tofile(str(path))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_labels(path: Path, width: int, height: int) -> list[np.ndarray]:
    boxes = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        class_id, x, y, w, h = raw.split()
        if int(class_id) != 0:
            raise ValueError(f"unexpected class in {path}")
        x, y, w, h = (float(value) for value in (x, y, w, h))
        boxes.append(
            np.asarray(
                [
                    [(x - w / 2) * width, (y - h / 2) * height],
                    [(x + w / 2) * width, (y - h / 2) * height],
                    [(x + w / 2) * width, (y + h / 2) * height],
                    [(x - w / 2) * width, (y + h / 2) * height],
                ],
                dtype=np.float32,
            )
        )
    return boxes


def add_panel_frame(
    content: np.ndarray, boxes: list[np.ndarray], rng: random.Random
) -> tuple[np.ndarray, list[np.ndarray], str]:
    height, width = content.shape[:2]
    style = rng.choice(["none", "white", "white", "black", "gray", "wood"])
    margin_ratio = 0.0 if style == "none" else rng.uniform(0.025, 0.13)
    margin = int(round(max(width, height) * margin_ratio))
    colors = {
        "none": (255, 255, 255),
        "white": (rng.randint(225, 255),) * 3,
        "black": (rng.randint(5, 35),) * 3,
        "gray": (rng.randint(80, 190),) * 3,
        "wood": (rng.randint(25, 65), rng.randint(70, 120), rng.randint(110, 170)),
    }
    panel = np.full((height + 2 * margin, width + 2 * margin, 3), colors[style], dtype=np.uint8)
    panel[margin : margin + height, margin : margin + width] = content
    shifted = [box + np.asarray([margin, margin], dtype=np.float32) for box in boxes]
    return panel, shifted, style


def destination_quad(
    panel_shape: tuple[int, int],
    background_shape: tuple[int, int],
    boxes: list[np.ndarray],
    rng: random.Random,
) -> np.ndarray:
    panel_h, panel_w = panel_shape
    bg_h, bg_w = background_shape
    if boxes:
        all_points = np.concatenate(boxes, axis=0)
        cat_w = max(1.0, float(all_points[:, 0].max() - all_points[:, 0].min()))
        cat_h = max(1.0, float(all_points[:, 1].max() - all_points[:, 1].min()))
        desired_short = rng.uniform(0.13, 0.43) * min(bg_w, bg_h)
        scale = desired_short / min(cat_w, cat_h)
    else:
        scale = rng.uniform(0.25, 0.65) * bg_w / panel_w
    scale = min(scale, 0.82 * bg_w / panel_w, 0.82 * bg_h / panel_h)
    scale = max(scale, min(0.20 * bg_w / panel_w, 0.20 * bg_h / panel_h))
    target_w = max(24.0, panel_w * scale)
    target_h = max(24.0, panel_h * scale)
    left = rng.uniform(0.03 * bg_w, max(0.03 * bg_w, bg_w - target_w - 0.03 * bg_w))
    top = rng.uniform(0.03 * bg_h, max(0.03 * bg_h, bg_h - target_h - 0.03 * bg_h))
    jitter_x = 0.09 * target_w
    jitter_y = 0.09 * target_h
    quad = np.asarray(
        [
            [left + rng.uniform(-jitter_x, jitter_x), top + rng.uniform(-jitter_y, jitter_y)],
            [left + target_w + rng.uniform(-jitter_x, jitter_x), top + rng.uniform(-jitter_y, jitter_y)],
            [left + target_w + rng.uniform(-jitter_x, jitter_x), top + target_h + rng.uniform(-jitter_y, jitter_y)],
            [left + rng.uniform(-jitter_x, jitter_x), top + target_h + rng.uniform(-jitter_y, jitter_y)],
        ],
        dtype=np.float32,
    )
    quad[:, 0] = np.clip(quad[:, 0], 1, bg_w - 2)
    quad[:, 1] = np.clip(quad[:, 1], 1, bg_h - 2)
    return quad


def composite_panel(
    *,
    content: np.ndarray,
    boxes: list[np.ndarray],
    background: np.ndarray,
    rng: random.Random,
) -> tuple[np.ndarray, list[tuple[float, float, float, float]], dict[str, object]]:
    panel, panel_boxes, frame_style = add_panel_frame(content, boxes, rng)
    panel_h, panel_w = panel.shape[:2]
    bg_h, bg_w = background.shape[:2]
    source_quad = np.asarray(
        [[0, 0], [panel_w - 1, 0], [panel_w - 1, panel_h - 1], [0, panel_h - 1]],
        dtype=np.float32,
    )
    destination = destination_quad((panel_h, panel_w), (bg_h, bg_w), panel_boxes, rng)
    homography = cv2.getPerspectiveTransform(source_quad, destination)
    warped = cv2.warpPerspective(panel, homography, (bg_w, bg_h), flags=cv2.INTER_LINEAR)
    mask_source = np.full((panel_h, panel_w), 255, dtype=np.uint8)
    mask = cv2.warpPerspective(mask_source, homography, (bg_w, bg_h), flags=cv2.INTER_LINEAR)
    alpha = (mask.astype(np.float32) / 255.0)[..., None]
    output = (warped.astype(np.float32) * alpha + background.astype(np.float32) * (1.0 - alpha)).astype(np.uint8)

    if rng.random() < 0.55:
        glare = np.zeros_like(output)
        x = int(rng.uniform(0, bg_w))
        width = int(rng.uniform(0.04, 0.14) * bg_w)
        polygon = np.asarray([[x, 0], [min(bg_w - 1, x + width), 0], [max(0, x - width), bg_h - 1], [max(0, x - 2 * width), bg_h - 1]])
        cv2.fillConvexPoly(glare, polygon, (255, 255, 255))
        output = cv2.addWeighted(output, 1.0, glare, rng.uniform(0.03, 0.13), 0)
    if rng.random() < 0.35:
        step = rng.randint(3, 8)
        overlay = output.copy()
        overlay[::step] = (overlay[::step].astype(np.float32) * rng.uniform(0.82, 0.95)).astype(np.uint8)
        output = overlay
    if rng.random() < 0.65:
        kernel = rng.choice([3, 3, 5])
        output = cv2.GaussianBlur(output, (kernel, kernel), rng.uniform(0.2, 1.1))
    contrast = rng.uniform(0.78, 1.18)
    brightness = rng.uniform(-18, 20)
    output = cv2.convertScaleAbs(output, alpha=contrast, beta=brightness)

    transformed_boxes: list[tuple[float, float, float, float]] = []
    for box in panel_boxes:
        transformed = cv2.perspectiveTransform(box.reshape(1, -1, 2), homography)[0]
        x1 = float(np.clip(transformed[:, 0].min(), 0, bg_w - 1))
        y1 = float(np.clip(transformed[:, 1].min(), 0, bg_h - 1))
        x2 = float(np.clip(transformed[:, 0].max(), 1, bg_w))
        y2 = float(np.clip(transformed[:, 1].max(), 1, bg_h))
        if x2 > x1 and y2 > y1:
            transformed_boxes.append((x1, y1, x2, y2))
    recipe = {
        "frame_style": frame_style,
        "jpeg_quality": rng.randint(48, 94),
        "destination_quad": destination.round(2).tolist(),
    }
    return output, transformed_boxes, recipe


def normalized_label(box: tuple[float, float, float, float], width: int, height: int) -> str:
    x1, y1, x2, y2 = box
    x = (x1 + x2) / (2 * width)
    y = (y1 + y2) / (2 * height)
    w = (x2 - x1) / width
    h = (y2 - y1) / height
    return f"0 {x:.6f} {y:.6f} {w:.6f} {h:.6f}"


def review_sheet(samples: list[dict[str, object]], output: Path, seed: int) -> None:
    rng = random.Random(seed)
    selected = rng.sample(samples, min(40, len(samples)))
    cols, cell_w, cell_h = 5, 320, 260
    sheet = Image.new("RGB", (cols * cell_w, math.ceil(len(selected) / cols) * cell_h), "white")
    font = ImageFont.load_default()
    for index, sample in enumerate(selected):
        path = Path(str(sample["output_image_absolute"]))
        with Image.open(path) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
        original_w, original_h = image.size
        label_path = Path(str(sample["output_label_absolute"]))
        boxes = parse_labels(label_path, original_w, original_h)
        draw = ImageDraw.Draw(image)
        for box in boxes:
            x1, y1 = box[:, 0].min(), box[:, 1].min()
            x2, y2 = box[:, 0].max(), box[:, 1].max()
            draw.rectangle((x1, y1, x2, y2), outline=(0, 230, 0), width=max(3, original_w // 250))
        image.thumbnail((cell_w - 8, cell_h - 30), Image.Resampling.LANCZOS)
        cell = Image.new("RGB", (cell_w, cell_h), "white")
        cell.paste(image, ((cell_w - image.width) // 2, 24 + (cell_h - 24 - image.height) // 2))
        ImageDraw.Draw(cell).text((4, 4), str(sample["sample_id"]), fill="black", font=font)
        sheet.paste(cell, ((index % cols) * cell_w, (index // cols) * cell_h))
    sheet.save(output, quality=92)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-data",
        type=Path,
        default=Path("data/downloads/detector_tuner_sphynx_pallas_negatives_yolo_20260715"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/downloads/detector_tuner_screenprint_yolo_20260715"),
    )
    parser.add_argument("--seed", type=int, default=20260715)
    parser.add_argument("--blank-negatives", type=int, default=160)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    base = args.base_data.resolve()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing output: {output}")
    materialize_tree(base, output)
    rng = random.Random(args.seed)
    (output / "data.yaml").write_text(
        f"path: {output.as_posix()}\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n\n"
        "names:\n"
        "  0: cat\n",
        encoding="utf-8",
    )

    with (base / "manifest.csv").open("r", newline="", encoding="utf-8") as handle:
        manifest = list(csv.DictReader(handle))
        fields = list(manifest[0])
    for optional in (
        "source_dataset",
        "annotation_source",
        "quality_flags",
        "source_group_id",
        "parent_sample_id",
        "transform",
        "materialization",
    ):
        if optional not in fields:
            fields.append(optional)
    for row in manifest:
        source_image = manifest_file(base, row, "image")
        source_label = manifest_file(base, row, "label")
        output_image = output / "images" / row["split"] / source_image.name
        output_label = output / "labels" / row["split"] / source_label.name
        row["output_image"] = project_path(output_image, root)
        row["output_label"] = project_path(output_label, root)
        row.setdefault("parent_sample_id", row["sample_id"])
        row.setdefault("transform", "identity")
        row.setdefault("materialization", "hardlink_or_copy")
    positives = [
        row
        for row in manifest
        if row["split"] == "train" and int(row["box_count"]) > 0
    ]
    background_rows = [
        row
        for row in manifest
        if row["split"] == "train" and int(row["box_count"]) == 0
    ]
    backgrounds = [manifest_file(output, row, "image") for row in background_rows]
    if not positives or not backgrounds:
        raise ValueError(f"empty inputs: positives={len(positives)}, backgrounds={len(backgrounds)}")

    synthetic_rows: list[dict[str, object]] = []
    for index, row in enumerate(positives, 1):
        content_path = manifest_file(output, row, "image")
        label_path = manifest_file(output, row, "label")
        background_path = rng.choice(backgrounds)
        content = read_bgr(content_path)
        background = read_bgr(background_path)
        boxes = parse_labels(label_path, content.shape[1], content.shape[0])
        composite, transformed, recipe = composite_panel(
            content=content, boxes=boxes, background=background, rng=rng
        )
        if not transformed:
            raise ValueError(f"lost all boxes for {content_path}")
        sample_id = f"synthetic-screen-{row['breed']}-{index:04d}"
        output_image = output / "images" / "train" / f"{sample_id}.jpg"
        output_label = output / "labels" / "train" / f"{sample_id}.txt"
        quality = int(recipe["jpeg_quality"])
        write_jpeg(output_image, composite, quality)
        output_label.write_text("\n".join(normalized_label(box, composite.shape[1], composite.shape[0]) for box in transformed) + "\n", encoding="utf-8")
        manifest.append(
            {
                "sample_id": sample_id,
                "breed": row["breed"],
                "split": "train",
                "source_dataset": row.get("source_dataset", ""),
                "source_image": project_path(content_path, root),
                "source_label": project_path(label_path, root),
                "output_image": project_path(output_image, root),
                "output_label": project_path(output_label, root),
                "width": composite.shape[1],
                "height": composite.shape[0],
                "box_count": len(transformed),
                "image_sha256": sha256(output_image),
                "label_sha256": sha256(output_label),
                "annotation_source": row.get("annotation_source", ""),
                "quality_flags": row.get("quality_flags", ""),
                "source_group_id": row.get("source_group_id", row["sample_id"]),
                "parent_sample_id": row["sample_id"],
                "transform": "screenprint_homography",
                "materialization": "generated",
            }
        )
        synthetic_rows.append(
            {
                "sample_id": sample_id,
                "kind": "screenprint_positive",
                "breed": row["breed"],
                "source_content": project_path(content_path, root),
                "source_background": project_path(background_path, root),
                "output_image": project_path(output_image, root),
                "output_label": project_path(output_label, root),
                "box_count": len(transformed),
                "recipe": json.dumps(recipe, separators=(",", ":")),
                "output_image_absolute": str(output_image),
                "output_label_absolute": str(output_label),
            }
        )

    for index in range(1, args.blank_negatives + 1):
        content_path = rng.choice(backgrounds)
        background_path = rng.choice(backgrounds)
        content = read_bgr(content_path)
        background = read_bgr(background_path)
        composite, transformed, recipe = composite_panel(
            content=content, boxes=[], background=background, rng=rng
        )
        if transformed:
            raise AssertionError("blank negative unexpectedly has boxes")
        sample_id = f"synthetic-blank-panel-{index:04d}"
        output_image = output / "images" / "train" / f"{sample_id}.jpg"
        output_label = output / "labels" / "train" / f"{sample_id}.txt"
        write_jpeg(output_image, composite, int(recipe["jpeg_quality"]))
        output_label.touch()
        manifest.append(
            {
                "sample_id": sample_id,
                "breed": "not_target",
                "split": "train",
                "source_dataset": "synthetic_blank_panel",
                "source_image": project_path(content_path, root),
                "source_label": "",
                "output_image": project_path(output_image, root),
                "output_label": project_path(output_label, root),
                "width": composite.shape[1],
                "height": composite.shape[0],
                "box_count": 0,
                "image_sha256": sha256(output_image),
                "label_sha256": hashlib.sha256(b"").hexdigest(),
                "annotation_source": "empty_background",
                "quality_flags": "",
                "source_group_id": f"synthetic-blank-panel-{index:04d}",
                "parent_sample_id": "",
                "transform": "blank_screenprint_homography",
                "materialization": "generated",
            }
        )
        synthetic_rows.append(
            {
                "sample_id": sample_id,
                "kind": "blank_panel_negative",
                "breed": "not_target",
                "source_content": project_path(content_path, root),
                "source_background": project_path(background_path, root),
                "output_image": project_path(output_image, root),
                "output_label": project_path(output_label, root),
                "box_count": 0,
                "recipe": json.dumps(recipe, separators=(",", ":")),
                "output_image_absolute": str(output_image),
                "output_label_absolute": str(output_label),
            }
        )

    with (output / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(manifest)
    public_synthetic_fields = [field for field in synthetic_rows[0] if not field.endswith("_absolute")]
    with (output / "synthetic_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=public_synthetic_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(synthetic_rows)
    positive_synthetic = [row for row in synthetic_rows if row["kind"] == "screenprint_positive"]
    review_sheet(positive_synthetic, output / "screenprint_positive_review_40.jpg", args.seed)

    report = {
        "schema_version": 1,
        "status": "READY_FOR_DETECTOR_TRAINING",
        "seed": args.seed,
        "train": {
            "original_positive_images": len(positives),
            "original_background_images": len(backgrounds),
            "synthetic_screenprint_positive_images": len(positive_synthetic),
            "synthetic_blank_panel_negatives": args.blank_negatives,
            "total_images": len(positives) + len(backgrounds) + len(positive_synthetic) + args.blank_negatives,
        },
        "held_out": {
            "positive_val": sum(row["split"] == "val" and int(row["box_count"]) > 0 for row in manifest),
            "positive_test": sum(row["split"] == "test" and int(row["box_count"]) > 0 for row in manifest),
            "not_target_val_and_val_cal": 54,
            "robot_camera_11_and_model_selection_24_used_for_training": False,
        },
        "notes": [
            "all positive boxes are propagated through the exact perspective homography",
            "blank panel negatives reduce frame/rectangle shortcut learning",
            "review sheet is evidence only and is not a training input",
        ],
    }
    (output / "augmentation_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
