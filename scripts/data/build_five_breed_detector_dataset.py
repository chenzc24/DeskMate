"""Build the unhashed-to-hashed five-breed detector base training view.

The returned Ragdoll/Singapura/Persian annotations already contain frozen
train/val/test assignments.  This command joins them with the reviewed BD05
Sphynx/Pallas positives and background negatives without changing either
source dataset.  Files are hard-linked when possible so the derived Ultralytics
view does not duplicate the canonical source bytes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
from collections import Counter
from pathlib import Path

from PIL import Image, ImageOps


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
BREED_GROUPS = {
    "0_ragdoll": "ragdoll",
    "1_singapura": "singapura",
    "2_persian": "persian",
}
MANIFEST_FIELDS = [
    "sample_id",
    "breed",
    "split",
    "source_dataset",
    "source_image",
    "source_label",
    "output_image",
    "output_label",
    "width",
    "height",
    "box_count",
    "image_sha256",
    "label_sha256",
    "annotation_source",
    "quality_flags",
    "source_group_id",
    "parent_sample_id",
    "transform",
    "materialization",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def project_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def parse_yolo_label(path: Path) -> list[tuple[int, float, float, float, float]]:
    boxes: list[tuple[int, float, float, float, float]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not raw.strip():
            continue
        pieces = raw.split()
        if len(pieces) != 5:
            raise ValueError(f"{path}:{line_number}: expected 5 YOLO fields")
        class_id = int(pieces[0])
        values = tuple(float(value) for value in pieces[1:])
        x, y, width, height = values
        if class_id != 0:
            raise ValueError(f"{path}:{line_number}: expected class 0, got {class_id}")
        if not all(math.isfinite(value) for value in values):
            raise ValueError(f"{path}:{line_number}: non-finite coordinates")
        if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < width <= 1 and 0 < height <= 1):
            raise ValueError(f"{path}:{line_number}: coordinates out of range")
        if x - width / 2 < -1e-6 or y - height / 2 < -1e-6:
            raise ValueError(f"{path}:{line_number}: box starts outside image")
        if x + width / 2 > 1 + 1e-6 or y + height / 2 > 1 + 1e-6:
            raise ValueError(f"{path}:{line_number}: box ends outside image")
        boxes.append((class_id, x, y, width, height))
    return boxes


def materialize(source: Path, target: Path) -> str:
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, target)
        return "hardlink"
    except OSError:
        shutil.copy2(source, target)
        return "copy"


def add_sample(
    *,
    project_root: Path,
    output: Path,
    source_dataset: str,
    image_path: Path,
    label_path: Path,
    sample_id: str,
    breed: str,
    split: str,
    annotation_source: str,
    quality_flags: str = "",
    source_group_id: str = "",
) -> dict[str, object]:
    if split not in {"train", "val", "test"}:
        raise ValueError(f"unsupported split {split!r} for {sample_id}")
    if image_path.suffix.lower() not in IMAGE_SUFFIXES:
        raise ValueError(f"unsupported image suffix: {image_path}")
    if not image_path.is_file() or not label_path.is_file():
        raise FileNotFoundError(f"missing image/label pair: {image_path}, {label_path}")
    boxes = parse_yolo_label(label_path)
    if breed != "not_target" and not boxes:
        raise ValueError(f"positive sample has no box: {sample_id}")
    if breed == "not_target" and boxes:
        raise ValueError(f"background sample has boxes: {sample_id}")
    with Image.open(image_path) as opened:
        image = ImageOps.exif_transpose(opened)
        image.verify()
        width, height = image.size
    output_image = output / "images" / split / f"{sample_id}{image_path.suffix.lower()}"
    output_label = output / "labels" / split / f"{sample_id}.txt"
    image_materialization = materialize(image_path, output_image)
    label_materialization = materialize(label_path, output_label)
    if image_materialization != label_materialization:
        materialization = f"image:{image_materialization};label:{label_materialization}"
    else:
        materialization = image_materialization
    return {
        "sample_id": sample_id,
        "breed": breed,
        "split": split,
        "source_dataset": source_dataset,
        "source_image": project_path(image_path, project_root),
        "source_label": project_path(label_path, project_root),
        "output_image": project_path(output_image, project_root),
        "output_label": project_path(output_label, project_root),
        "width": width,
        "height": height,
        "box_count": len(boxes),
        "image_sha256": sha256_file(output_image),
        "label_sha256": sha256_file(output_label),
        "annotation_source": annotation_source,
        "quality_flags": quality_flags,
        "source_group_id": source_group_id or sample_id,
        "parent_sample_id": sample_id,
        "transform": "identity",
        "materialization": materialization,
    }


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def build_dataset(
    *,
    project_root: Path,
    bd05_base: Path,
    three_breed: Path,
    selection_manifest: Path,
    output: Path,
) -> dict[str, object]:
    project_root = project_root.resolve()
    bd05_base = bd05_base.resolve()
    three_breed = three_breed.resolve()
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output}")
    output.mkdir(parents=True)

    rows: list[dict[str, object]] = []
    sample_ids: set[str] = set()
    filenames: set[str] = set()

    for source in load_csv(bd05_base / "manifest.csv"):
        sample_id = source["sample_id"]
        split = source["split"]
        image_candidates = list((bd05_base / "images" / split).glob(f"{sample_id}.*"))
        image_candidates = [path for path in image_candidates if path.suffix.lower() in IMAGE_SUFFIXES]
        if len(image_candidates) != 1:
            raise ValueError(f"expected one BD05 image for {sample_id}, found {image_candidates}")
        image_path = image_candidates[0]
        label_path = bd05_base / "labels" / split / f"{sample_id}.txt"
        annotation_source = "reviewed_background" if source["breed"] == "not_target" else "manual_box"
        row = add_sample(
            project_root=project_root,
            output=output,
            source_dataset="bd05_manual_curated_base_20260715",
            image_path=image_path,
            label_path=label_path,
            sample_id=sample_id,
            breed=source["breed"],
            split=split,
            annotation_source=annotation_source,
            source_group_id=sample_id,
        )
        rows.append(row)
        sample_ids.add(sample_id)
        filenames.add(Path(str(row["output_image"])).name)

    for source in load_csv(three_breed / "manifest.csv"):
        sample_id = Path(source["export_image"]).stem
        breed = BREED_GROUPS.get(source["breed_group"])
        if breed is None:
            raise ValueError(f"unknown breed group: {source['breed_group']}")
        if sample_id in sample_ids:
            raise ValueError(f"duplicate sample id across source datasets: {sample_id}")
        image_path = three_breed / source["export_image"]
        label_path = three_breed / source["export_label"]
        if image_path.name in filenames:
            raise ValueError(f"duplicate output filename across source datasets: {image_path.name}")
        row = add_sample(
            project_root=project_root,
            output=output,
            source_dataset="returned_three_breed_annotations_20260716",
            image_path=image_path,
            label_path=label_path,
            sample_id=sample_id,
            breed=breed,
            split=source["split"],
            annotation_source=source["box_sources"],
            quality_flags=source["quality_flags"],
            source_group_id=source["relative_path"],
        )
        rows.append(row)
        sample_ids.add(sample_id)
        filenames.add(image_path.name)

    with (output / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    (output / "data.yaml").write_text(
        f"path: {output.as_posix()}\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n\n"
        "names:\n"
        "  0: cat\n",
        encoding="utf-8",
    )

    diagnostic_hashes = {
        row["source_sha256"] for row in load_csv(selection_manifest)
    }
    overlap = sorted(
        str(row["sample_id"])
        for row in rows
        if str(row["image_sha256"]) in diagnostic_hashes
    )
    counts = Counter(
        (str(row["breed"]), str(row["split"])) for row in rows
    )
    boxes = Counter(
        (str(row["breed"]), str(row["split"]))
        for row in rows
        for _ in range(int(row["box_count"]))
    )
    report = {
        "schema_version": 1,
        "status": "READY_FOR_SCREENPRINT_AUGMENTATION",
        "source_manifests": {
            "bd05_base": sha256_file(bd05_base / "manifest.csv"),
            "three_breed": sha256_file(three_breed / "manifest.csv"),
            "selection_24": sha256_file(selection_manifest),
        },
        "counts": {
            breed: {
                split: {
                    "images": counts[(breed, split)],
                    "boxes": boxes[(breed, split)],
                }
                for split in ("train", "val", "test")
            }
            for breed in ("ragdoll", "singapura", "persian", "sphynx", "pallas", "not_target")
        },
        "totals": {
            "images": len(rows),
            "boxes": sum(int(row["box_count"]) for row in rows),
            "train_images": sum(str(row["split"]) == "train" for row in rows),
            "val_images": sum(str(row["split"]) == "val" for row in rows),
            "test_images": sum(str(row["split"]) == "test" for row in rows),
        },
        "diagnostic_24_exact_overlap": overlap,
        "manifest_sha256": sha256_file(output / "manifest.csv"),
        "materialization": dict(Counter(str(row["materialization"]) for row in rows)),
    }
    (output / "preparation_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bd05-base",
        type=Path,
        default=Path("data/downloads/detector_tuner_manual_curated_base_yolo_20260715"),
    )
    parser.add_argument(
        "--three-breed",
        type=Path,
        default=Path("data/downloads/ultralytics_yolo_detection/ultralytics_yolo_detection"),
    )
    parser.add_argument(
        "--selection-manifest",
        type=Path,
        default=Path("data/downloads/Camera/model_test_selection_20260715/manifest.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/work/detector-five-breed-base-20260716"),
    )
    args = parser.parse_args()
    report = build_dataset(
        project_root=Path.cwd(),
        bd05_base=args.bd05_base,
        three_breed=args.three_breed,
        selection_manifest=args.selection_manifest,
        output=args.output,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
