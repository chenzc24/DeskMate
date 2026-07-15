from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
LABELS = ("ragdoll", "singapura", "persian", "sphynx", "pallas")
CLASS_DIRS = {label: f"{index}_{label}" for index, label in enumerate(LABELS)}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def materialize(source: Path, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
        return "hardlink"
    except OSError:
        shutil.copy2(source, destination)
        return "copy"


def read_image(path: Path) -> np.ndarray:
    image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"cannot decode image: {path}")
    return image


def motion_blur(image: np.ndarray, length: int, angle: float) -> np.ndarray:
    kernel = np.zeros((length, length), dtype=np.float32)
    kernel[length // 2, :] = 1.0
    rotation = cv2.getRotationMatrix2D(
        ((length - 1) / 2.0, (length - 1) / 2.0), angle, 1.0
    )
    kernel = cv2.warpAffine(kernel, rotation, (length, length))
    kernel /= max(float(kernel.sum()), 1e-6)
    return cv2.filter2D(image, -1, kernel)


def augment_camera_view(image: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    height, width = image.shape[:2]
    center = (width / 2.0, height / 2.0)
    affine = cv2.getRotationMatrix2D(
        center, float(rng.uniform(-12.0, 12.0)), float(rng.uniform(0.82, 1.18))
    )
    shear = math.tan(math.radians(float(rng.uniform(-4.0, 4.0))))
    affine[0, 1] += shear
    affine[0, 2] += float(rng.uniform(-0.12, 0.12) * width)
    affine[1, 2] += float(rng.uniform(-0.12, 0.12) * height)
    result = cv2.warpAffine(
        image,
        affine,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT_101,
    )
    if rng.random() < 0.45:
        strength = 0.025
        source = np.float32(
            [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]]
        )
        jitter = np.column_stack(
            (
                rng.uniform(-strength, strength, 4) * width,
                rng.uniform(-strength, strength, 4) * height,
            )
        ).astype(np.float32)
        perspective = cv2.getPerspectiveTransform(source, source + jitter)
        result = cv2.warpPerspective(
            result,
            perspective,
            (width, height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT_101,
        )
    hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 0] = (hsv[..., 0] + rng.uniform(-7.0, 7.0)) % 180.0
    hsv[..., 1] *= float(rng.uniform(0.72, 1.28))
    hsv[..., 2] *= float(rng.uniform(0.72, 1.28))
    hsv[..., 1:] = np.clip(hsv[..., 1:], 0, 255)
    result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    gamma = float(rng.uniform(0.72, 1.38))
    lookup = np.asarray(
        [min(255, round(((value / 255.0) ** gamma) * 255.0)) for value in range(256)],
        dtype=np.uint8,
    )
    result = cv2.LUT(result, lookup)
    result = cv2.convertScaleAbs(
        result, alpha=float(rng.uniform(0.82, 1.18)), beta=float(rng.uniform(-18, 18))
    )
    blur_draw = rng.random()
    if blur_draw < 0.25:
        length = int(rng.choice([3, 5, 7, 9]))
        result = motion_blur(result, length, float(rng.uniform(0, 180)))
    elif blur_draw < 0.45:
        kernel = int(rng.choice([3, 5]))
        result = cv2.GaussianBlur(result, (kernel, kernel), float(rng.uniform(0.3, 1.4)))
    if rng.random() < 0.35:
        factor = float(rng.uniform(0.55, 0.88))
        small = cv2.resize(
            result,
            (max(32, round(width * factor)), max(32, round(height * factor))),
            interpolation=cv2.INTER_AREA,
        )
        result = cv2.resize(small, (width, height), interpolation=cv2.INTER_LINEAR)
    if rng.random() < 0.55:
        sigma = float(rng.uniform(1.0, 7.0))
        noise = rng.normal(0.0, sigma, result.shape).astype(np.float32)
        result = np.clip(result.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    if rng.random() < 0.20:
        cut_width = max(4, round(width * rng.uniform(0.03, 0.10)))
        cut_height = max(4, round(height * rng.uniform(0.03, 0.10)))
        left = int(rng.integers(0, max(1, width - cut_width + 1)))
        top = int(rng.integers(0, max(1, height - cut_height + 1)))
        fill = tuple(int(value) for value in result.mean(axis=(0, 1)))
        cv2.rectangle(
            result,
            (left, top),
            (left + cut_width, top + cut_height),
            fill,
            thickness=-1,
        )
    return result


def deterministic_rng(seed: int, sample_id: str, variant: int) -> np.random.Generator:
    payload = f"{seed}:{sample_id}:{variant}".encode("utf-8")
    value = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    return np.random.default_rng(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / "data/downloads/baseline_target5_machine_merged_20260715",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/downloads/baseline_target5_clean_augmented_20260715",
    )
    parser.add_argument("--target-train-count-per-class", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=20260715)
    parser.add_argument(
        "--diagnostic-manifest",
        type=Path,
        default=ROOT / "data/downloads/Camera/model_test_selection_20260715/manifest.csv",
    )
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    source_dataset = source / "one_view_yolo_classify"
    dataset = output / "one_view_yolo_classify"
    with (source / "target5_manifest.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        source_rows = list(csv.DictReader(handle))
    if any(row["label"] not in LABELS for row in source_rows):
        raise RuntimeError("source contains a non-target label")
    diagnostic_hashes: set[str] = set()
    with args.diagnostic_manifest.resolve().open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        diagnostic_hashes = {row["source_sha256"] for row in csv.DictReader(handle)}
    train_source_overlap = sum(
        row["split"] == "train" and row["source_sha256"] in diagnostic_hashes
        for row in source_rows
    )
    if train_source_overlap:
        raise RuntimeError("diagnostic source leaked into clean training source")
    rows: list[dict[str, object]] = []
    methods: Counter[str] = Counter()
    train_by_label: dict[str, list[dict[str, str]]] = defaultdict(list)
    for source_row in source_rows:
        label = source_row["label"]
        split = source_row["split"]
        relative = Path(source_row["dataset_relative_path"])
        source_path = source_dataset / relative
        destination = dataset / relative
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        methods[materialize(source_path, destination)] += 1
        rows.append(
            {
                "sample_id": source_row["sample_id"],
                "label": label,
                "split": split,
                "source_kind": source_row["source_kind"],
                "parent_sample_id": source_row["sample_id"],
                "augmentation_index": 0,
                "source_path": source_row["source_path"],
                "source_sha256": source_row["source_sha256"],
                "dataset_relative_path": relative.as_posix(),
                "view_sha256": sha256_file(destination),
            }
        )
        if split == "train":
            train_by_label[label].append(source_row)
    augmented_counts: Counter[str] = Counter()
    for label in LABELS:
        sources = sorted(train_by_label[label], key=lambda row: row["sample_id"])
        needed = args.target_train_count_per_class - len(sources)
        if needed < len(sources):
            raise ValueError(
                "target count must permit at least one augmentation of every training sample"
            )
        per_parent: Counter[str] = Counter()
        for ordinal in range(needed):
            source_row = sources[ordinal % len(sources)]
            sample_id = source_row["sample_id"]
            per_parent[sample_id] += 1
            variant = per_parent[sample_id]
            source_path = source_dataset / Path(source_row["dataset_relative_path"])
            image = read_image(source_path)
            augmented = augment_camera_view(
                image, deterministic_rng(args.seed, sample_id, variant)
            )
            destination = (
                dataset
                / "train"
                / CLASS_DIRS[label]
                / f"aug-{label}-{ordinal + 1:05d}.jpg"
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            quality_rng = deterministic_rng(args.seed + 1, sample_id, variant)
            quality = int(quality_rng.integers(48, 93))
            success, encoded = cv2.imencode(
                ".jpg", augmented, [cv2.IMWRITE_JPEG_QUALITY, quality]
            )
            if not success:
                raise RuntimeError(f"cannot encode augmentation: {source_path}")
            encoded.tofile(str(destination))
            rows.append(
                {
                    "sample_id": f"aug-{label}-{ordinal + 1:05d}",
                    "label": label,
                    "split": "train",
                    "source_kind": "offline_camera_augmentation",
                    "parent_sample_id": sample_id,
                    "augmentation_index": variant,
                    "source_path": str(source_path),
                    "source_sha256": source_row["source_sha256"],
                    "dataset_relative_path": destination.relative_to(dataset).as_posix(),
                    "view_sha256": sha256_file(destination),
                }
            )
            augmented_counts[label] += 1
    output.mkdir(parents=True, exist_ok=True)
    manifest = output / "augmented_manifest.csv"
    with manifest.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    counts = Counter((str(row["split"]), str(row["label"])) for row in rows)
    final_counts = {
        split: {label: counts[(split, label)] for label in LABELS}
        for split in ("train", "val", "val_cal")
    }
    report = {
        "schema_version": 1,
        "status": "TARGET5_AUGMENTED_DATASET_READY",
        "source_root": str(source),
        "dataset_root": str(dataset),
        "manifest": str(manifest),
        "manifest_sha256": sha256_file(manifest),
        "labels": list(LABELS),
        "not_target_present": False,
        "robot_burst_adaptation_rows_present": 0,
        "diagnostic_rows_present": 0,
        "diagnostic_exact_source_overlap": train_source_overlap,
        "all_training_parents_augmented_at_least_once": True,
        "augmented_samples_are_not_independent_data": True,
        "target_train_count_per_class": args.target_train_count_per_class,
        "original_counts": {
            split: {
                label: sum(
                    row["split"] == split and row["label"] == label
                    for row in source_rows
                )
                for label in LABELS
            }
            for split in ("train", "val", "val_cal")
        },
        "augmented_train_counts": dict(augmented_counts),
        "final_counts": final_counts,
        "total": len(rows),
        "materialization": dict(methods),
        "augmentation_seed": args.seed,
        "augmentation_families": [
            "affine_rotation_scale_translation_shear",
            "mild_perspective",
            "hsv_exposure_gamma_contrast",
            "motion_or_gaussian_blur",
            "downsample_upsample",
            "sensor_noise",
            "jpeg_compression",
            "small_cutout",
        ],
    }
    (output / "augmented_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
