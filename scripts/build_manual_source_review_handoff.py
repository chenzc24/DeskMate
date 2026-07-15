"""Create an isolated, deletion-driven manual review package of source images."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
CLASS_DIRS = ("0_ragdoll", "1_singapura", "2_persian", "3_sphynx", "4_pallas")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def copy_image(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/downloads/manual_source_review_20260715"),
    )
    args = parser.parse_args()
    root = Path.cwd().resolve()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing review package: {output}")

    classifier_source = root / (
        "data/downloads/baseline_target5_machine_merged_20260715/"
        "one_view_yolo_classify/train"
    )
    sphynx_images = root / "data/downloads/detector_tuner_yolo_20260715/images/train"
    sphynx_labels = root / "data/downloads/detector_tuner_yolo_20260715/labels/train"
    pallas_images = root / "data/downloads/Pallas-cat-yolo/Pallas-cat-yolo/images/train"
    pallas_labels = root / "data/downloads/Pallas-cat-yolo/Pallas-cat-yolo/labels/train"
    negative_source = root / (
        "data/downloads/baseline_merged_gapfill_nocat_20260715/"
        "one_view_yolo_classify/train/5_not_target"
    )

    rows: list[dict[str, object]] = []
    classifier_counts: dict[str, int] = {}
    for class_dir in CLASS_DIRS:
        sources = sorted(
            path
            for path in (classifier_source / class_dir).iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        )
        classifier_counts[class_dir] = len(sources)
        for source in sources:
            destination = output / "01_classifier_m8_original" / class_dir / source.name
            copy_image(source, destination)
            rows.append(
                {
                    "scope": "classifier_m8_original",
                    "label": class_dir.split("_", 1)[1],
                    "sample_id": source.stem,
                    "original_image": rel(source, root),
                    "original_label": "",
                    "review_image": rel(destination, root),
                    "review_label": "",
                    "image_sha256": sha256(source),
                    "instruction": "keep, delete, or move to the correct class directory",
                }
            )

    detector_counts: dict[str, int] = {}
    for breed, images_dir, labels_dir in (
        ("sphynx", sphynx_images, sphynx_labels),
        ("pallas", pallas_images, pallas_labels),
    ):
        sources = sorted(
            path for path in images_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        )
        detector_counts[breed] = len(sources)
        for source in sources:
            label_source = labels_dir / f"{source.stem}.txt"
            if not label_source.is_file():
                raise ValueError(f"missing detector label: {label_source}")
            image_destination = output / "02_detector_positive" / breed / "images" / source.name
            label_destination = output / "02_detector_positive" / breed / "labels" / label_source.name
            copy_image(source, image_destination)
            label_destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(label_source, label_destination)
            rows.append(
                {
                    "scope": "detector_positive",
                    "label": breed,
                    "sample_id": source.stem,
                    "original_image": rel(source, root),
                    "original_label": rel(label_source, root),
                    "review_image": rel(image_destination, root),
                    "review_label": rel(label_destination, root),
                    "image_sha256": sha256(source),
                    "instruction": "keep or delete image; orphan label will be ignored after review",
                }
            )

    negatives = sorted(
        path for path in negative_source.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )
    for source in negatives:
        destination = output / "03_detector_negative_not_target" / source.name
        copy_image(source, destination)
        rows.append(
            {
                "scope": "detector_negative_not_target",
                "label": "not_target",
                "sample_id": source.stem,
                "original_image": rel(source, root),
                "original_label": "",
                "review_image": rel(destination, root),
                "review_label": "",
                "image_sha256": sha256(source),
                "instruction": "delete if any real, printed, or on-screen cat is visible",
            }
        )

    manifest = output / "review_manifest.csv"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    report = {
        "schema_version": 1,
        "status": "READY_FOR_MANUAL_SOURCE_REVIEW",
        "review_semantics": "remaining files are accepted; deleted files are rejected",
        "classifier_original_counts": classifier_counts,
        "detector_positive_counts": detector_counts,
        "detector_negative_count": len(negatives),
        "total_review_images": len(rows),
        "source_data_and_existing_models_modified": False,
        "post_review": {
            "classifier": "rebuild from surviving/moved originals, then apply the existing M8 augmentation families to 1200 per class",
            "detector": "rebuild from surviving positives and negatives, then apply the existing BD04 screen/print homography augmentation and blank-panel negatives",
            "fixed_seed": 20260715,
        },
    }
    (output / "review_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    instructions = """# Manual source review instructions

This directory is an isolated copy. The existing datasets, checkpoints, and
source files are not modified by deleting files here.

## 01_classifier_m8_original

- Keep a file if the visible cat clearly belongs to the directory breed.
- Delete unusable, ambiguous, tiny, heavily obstructed, or wrong-breed images.
- If the breed is clearly wrong but known, move the image to the correct class
  directory instead of deleting it.
- Do not rename files unless necessary.

## 02_detector_positive

- Keep usable cat images and inspect the matching YOLO label if a box looks bad.
- Delete the image to reject it. A remaining orphan label will be ignored.
- Breed correctness is less important here because the detector has one `cat`
  class, but non-cat images and bad boxes must be rejected.

## 03_detector_negative_not_target

- Delete any image containing a real cat, printed cat, screen cat, cat poster,
  cat toy, or convincing cat-like artwork.
- Keep genuine no-cat backgrounds and objects.

After review, do not run augmentation manually. Report completion and the
remaining files will be audited before the clean datasets are rebuilt with the
same augmentation logic and seed as M8/BD04.
"""
    (output / "README.md").write_text(instructions, encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
