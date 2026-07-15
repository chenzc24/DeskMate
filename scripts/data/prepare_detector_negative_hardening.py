"""Add held-in not-target backgrounds to the joint cat detector dataset."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--positive-data",
        type=Path,
        default=Path("data/downloads/detector_tuner_sphynx_pallas_yolo_20260715"),
    )
    parser.add_argument(
        "--negative-train",
        type=Path,
        default=Path(
            "data/downloads/baseline_merged_gapfill_nocat_20260715/"
            "one_view_yolo_classify/train/5_not_target"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/downloads/detector_tuner_sphynx_pallas_negatives_yolo_20260715"),
    )
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    root = args.project_root.resolve()
    positive_data = args.positive_data.resolve()
    negative_train = args.negative_train.resolve()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing output: {output}")

    shutil.copytree(positive_data, output)
    manifest_path = output / "manifest.csv"
    with manifest_path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        fields = list(rows[0])

    existing_ids = {str(row["sample_id"]) for row in rows}
    negatives = sorted(
        path for path in negative_train.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )
    for image_path in negatives:
        if image_path.stem in existing_ids:
            raise ValueError(f"duplicate sample id: {image_path.stem}")
        with Image.open(image_path) as image:
            image.verify()
        with Image.open(image_path) as image:
            width, height = image.size
        output_image = output / "images" / "train" / image_path.name
        output_label = output / "labels" / "train" / f"{image_path.stem}.txt"
        shutil.copy2(image_path, output_image)
        output_label.touch()
        rows.append(
            {
                "sample_id": image_path.stem,
                "breed": "not_target",
                "split": "train",
                "source_image": relative(image_path, root),
                "source_label": "",
                "output_image": relative(output_image, root),
                "output_label": relative(output_label, root),
                "width": width,
                "height": height,
                "box_count": 0,
                "image_sha256": sha256(image_path),
                "label_sha256": hashlib.sha256(b"").hexdigest(),
            }
        )

    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    data_yaml = (
        f"path: {output.as_posix()}\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n\n"
        "names:\n"
        "  0: cat\n"
    )
    (output / "data.yaml").write_text(data_yaml, encoding="utf-8")

    base_report = json.loads((positive_data / "preparation_report.json").read_text(encoding="utf-8"))
    report = {
        "schema_version": 1,
        "status": "READY_FOR_NEGATIVE_HARDENED_TRAINING",
        "base_dataset": relative(positive_data, root),
        "class_names": {"0": "cat"},
        "train": {
            "positive_images": 565,
            "background_images_with_empty_labels": len(negatives),
            "total_images": 565 + len(negatives),
            "positive_boxes": 566,
        },
        "validation": {
            "positive_images": 68,
            "not_target_images_held_out_elsewhere": 54,
        },
        "test": {"positive_images": 49},
        "negative_policy": {
            "source": relative(negative_train, root),
            "label": "empty YOLO label file means background/no cat",
            "held_out_val_and_val_cal_not_target_are_not_copied_into_training": True,
        },
        "base_positive_report": base_report,
    }
    (output / "preparation_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
