"""Validate and merge the Sphynx and Pallas YOLO detector datasets.

The two breeds are deliberately mapped to one detector class: ``0: cat``.
The existing Sphynx split is preserved. Pallas' provided train split remains
train, while its provided validation split is deterministically divided into
validation and test halves.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import shutil
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
SPLITS = ("train", "val", "test")
MANIFEST_FIELDS = (
    "sample_id",
    "breed",
    "split",
    "source_image",
    "source_label",
    "output_image",
    "output_label",
    "width",
    "height",
    "box_count",
    "image_sha256",
    "label_sha256",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def parse_label(path: Path) -> list[tuple[int, float, float, float, float]]:
    boxes: list[tuple[int, float, float, float, float]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 5:
            raise ValueError(f"{path}:{line_number}: expected 5 fields, got {len(parts)}")
        class_id = int(parts[0])
        values = tuple(float(value) for value in parts[1:])
        if class_id != 0:
            raise ValueError(f"{path}:{line_number}: expected class 0, got {class_id}")
        if not all(0.0 <= value <= 1.0 for value in values):
            raise ValueError(f"{path}:{line_number}: normalized coordinates out of range")
        x, y, w, h = values
        if w <= 0.0 or h <= 0.0:
            raise ValueError(f"{path}:{line_number}: width and height must be positive")
        if x - w / 2 < -1e-6 or y - h / 2 < -1e-6 or x + w / 2 > 1.0 + 1e-6 or y + h / 2 > 1.0 + 1e-6:
            raise ValueError(f"{path}:{line_number}: box extends outside normalized image")
        boxes.append((class_id, x, y, w, h))
    if not boxes:
        raise ValueError(f"{path}: empty label")
    return boxes


def paired_samples(images_dir: Path, labels_dir: Path) -> list[tuple[Path, Path]]:
    images = {path.stem: path for path in images_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES}
    labels = {path.stem: path for path in labels_dir.glob("*.txt")}
    if set(images) != set(labels):
        missing_labels = sorted(set(images) - set(labels))
        missing_images = sorted(set(labels) - set(images))
        raise ValueError(
            f"pair mismatch under {images_dir.parent}: missing labels={missing_labels[:10]}, "
            f"missing images={missing_images[:10]}"
        )
    return [(images[stem], labels[stem]) for stem in sorted(images)]


def validate_source_sample(image_path: Path, label_path: Path) -> tuple[int, int, list[tuple[int, float, float, float, float]]]:
    with Image.open(image_path) as image:
        image.verify()
    with Image.open(image_path) as image:
        width, height = image.size
    if width <= 0 or height <= 0:
        raise ValueError(f"{image_path}: invalid image dimensions")
    return width, height, parse_label(label_path)


def copy_sample(
    *,
    image_path: Path,
    label_path: Path,
    breed: str,
    split: str,
    output: Path,
    project_root: Path,
) -> dict[str, str | int]:
    width, height, boxes = validate_source_sample(image_path, label_path)
    output_image = output / "images" / split / image_path.name
    output_label = output / "labels" / split / f"{image_path.stem}.txt"
    if output_image.exists() or output_label.exists():
        raise ValueError(f"duplicate output sample id: {image_path.stem}")
    shutil.copy2(image_path, output_image)
    shutil.copy2(label_path, output_label)
    return {
        "sample_id": image_path.stem,
        "breed": breed,
        "split": split,
        "source_image": relative(image_path, project_root),
        "source_label": relative(label_path, project_root),
        "output_image": relative(output_image, project_root),
        "output_label": relative(output_label, project_root),
        "width": width,
        "height": height,
        "box_count": len(boxes),
        "image_sha256": sha256(image_path),
        "label_sha256": sha256(label_path),
    }


def draw_review(rows: list[dict[str, str | int]], project_root: Path, output_path: Path, seed: int) -> None:
    chosen: list[dict[str, str | int]] = []
    rng = random.Random(seed)
    for breed in ("sphynx", "pallas"):
        for split in SPLITS:
            pool = [row for row in rows if row["breed"] == breed and row["split"] == split]
            chosen.extend(rng.sample(pool, min(5, len(pool))))

    cell_w, cell_h = 320, 270
    cols = 5
    rows_count = (len(chosen) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows_count * cell_h), "white")
    font = ImageFont.load_default()
    for index, row in enumerate(chosen):
        image_path = project_root / str(row["output_image"])
        label_path = project_root / str(row["output_label"])
        with Image.open(image_path) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
        image.thumbnail((cell_w - 8, cell_h - 34), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (cell_w, cell_h), "white")
        left = (cell_w - image.width) // 2
        top = 24 + (cell_h - 24 - image.height) // 2
        canvas.paste(image, (left, top))
        draw = ImageDraw.Draw(canvas)
        for _, x, y, w, h in parse_label(label_path):
            x1 = left + (x - w / 2) * image.width
            y1 = top + (y - h / 2) * image.height
            x2 = left + (x + w / 2) * image.width
            y2 = top + (y + h / 2) * image.height
            draw.rectangle((x1, y1, x2, y2), outline=(0, 210, 0), width=3)
        title = f"{row['breed']} | {row['split']} | {row['sample_id']}"
        draw.text((5, 5), title, fill="black", font=font)
        sheet.paste(canvas, ((index % cols) * cell_w, (index // cols) * cell_h))
    sheet.save(output_path, quality=92)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sphynx", type=Path, required=True)
    parser.add_argument("--pallas", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--seed", type=int, default=20260715)
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    sphynx = args.sphynx.resolve()
    pallas = args.pallas.resolve()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing output: {output}")
    for split in SPLITS:
        (output / "images" / split).mkdir(parents=True)
        (output / "labels" / split).mkdir(parents=True)

    rows: list[dict[str, str | int]] = []
    for split in SPLITS:
        for image_path, label_path in paired_samples(sphynx / "images" / split, sphynx / "labels" / split):
            rows.append(
                copy_sample(
                    image_path=image_path,
                    label_path=label_path,
                    breed="sphynx",
                    split=split,
                    output=output,
                    project_root=project_root,
                )
            )

    pallas_train = paired_samples(pallas / "images" / "train", pallas / "labels" / "train")
    pallas_holdout = paired_samples(pallas / "images" / "val", pallas / "labels" / "val")
    rng = random.Random(args.seed)
    rng.shuffle(pallas_holdout)
    pallas_val = pallas_holdout[: len(pallas_holdout) // 2]
    pallas_test = pallas_holdout[len(pallas_holdout) // 2 :]
    for split, samples in (("train", pallas_train), ("val", pallas_val), ("test", pallas_test)):
        for image_path, label_path in samples:
            rows.append(
                copy_sample(
                    image_path=image_path,
                    label_path=label_path,
                    breed="pallas",
                    split=split,
                    output=output,
                    project_root=project_root,
                )
            )

    yaml_text = (
        f"path: {output.as_posix()}\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n\n"
        "names:\n"
        "  0: cat\n"
    )
    (output / "data.yaml").write_text(yaml_text, encoding="utf-8")
    with (output / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    image_counts = Counter((str(row["breed"]), str(row["split"])) for row in rows)
    box_counts: Counter[tuple[str, str]] = Counter()
    multi_counts: Counter[tuple[str, str]] = Counter()
    for row in rows:
        key = (str(row["breed"]), str(row["split"]))
        box_counts[key] += int(row["box_count"])
        if int(row["box_count"]) > 1:
            multi_counts[key] += 1
    report = {
        "schema_version": 1,
        "status": "READY_FOR_JOINT_TRAINING",
        "seed": args.seed,
        "class_names": {"0": "cat"},
        "policy": {
            "sphynx_split": "preserved from prepared dataset",
            "pallas_train": "preserved from colleague package",
            "pallas_original_val": "deterministically split 30 val / 30 test",
            "breed_mapping": "Sphynx and Pallas are both detector class 0: cat",
        },
        "counts": {
            breed: {
                split: {
                    "images": image_counts[(breed, split)],
                    "boxes": box_counts[(breed, split)],
                    "multi_box_images": multi_counts[(breed, split)],
                }
                for split in SPLITS
            }
            for breed in ("sphynx", "pallas")
        },
        "totals": {
            "images": len(rows),
            "boxes": sum(int(row["box_count"]) for row in rows),
        },
        "artifacts": {
            "data_yaml": "data.yaml",
            "manifest": "manifest.csv",
            "review_sheet": "annotation_review_30.jpg",
        },
    }
    (output / "preparation_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    draw_review(rows, project_root, output / "annotation_review_30.jpg", args.seed)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
