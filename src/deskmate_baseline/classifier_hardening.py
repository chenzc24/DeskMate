"""Deterministic class-balanced and printed-page classifier datasets."""

from __future__ import annotations

import csv
import hashlib
import os
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import cv2
import numpy as np

from .contracts import INTERNAL_LABELS


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _seed(value: str) -> int:
    return int.from_bytes(hashlib.sha256(value.encode("utf-8")).digest()[:8], "big")


def _ordered(paths: Sequence[Path], *, key: str) -> list[Path]:
    return sorted(
        paths,
        key=lambda path: hashlib.sha256(f"{key}:{path.name}".encode()).hexdigest(),
    )


def _link_or_copy(source: Path, destination: Path) -> None:
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def _fit_image(image: np.ndarray, width: int, height: int) -> np.ndarray:
    scale = min(width / image.shape[1], height / image.shape[0])
    resized = cv2.resize(
        image,
        (max(1, round(image.shape[1] * scale)), max(1, round(image.shape[0] * scale))),
        interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC,
    )
    canvas = np.full((height, width, 3), 238, dtype=np.uint8)
    top = (height - resized.shape[0]) // 2
    left = (width - resized.shape[1]) // 2
    canvas[top : top + resized.shape[0], left : left + resized.shape[1]] = resized
    return canvas


def render_printed_page(
    source: Path,
    destination: Path,
    *,
    seed_key: str,
    width: int = 640,
    height: int = 480,
    minimum_jpeg_quality: int = 55,
    maximum_jpeg_quality: int = 85,
) -> None:
    """Render one label-free printed-page/camera-domain training view."""
    image = cv2.imread(str(source), cv2.IMREAD_COLOR)
    if image is None or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(f"could not decode source image: {source}")
    if not 1 <= minimum_jpeg_quality <= maximum_jpeg_quality <= 100:
        raise ValueError("invalid JPEG quality range")
    rng = np.random.default_rng(_seed(seed_key))

    base = np.empty((height, width, 3), dtype=np.float32)
    color = np.asarray(
        [rng.integers(80, 165), rng.integers(80, 165), rng.integers(80, 165)],
        dtype=np.float32,
    )
    horizontal = np.linspace(-18, 18, width, dtype=np.float32)[None, :, None]
    noise = rng.normal(0, 4.0, (height, width, 1)).astype(np.float32)
    base[:] = color
    base += horizontal + noise
    background = np.clip(base, 0, 255).astype(np.uint8)

    page_width, page_height = max(16, round(width * 0.73)), max(16, round(height * 0.73))
    page_tone = int(rng.integers(225, 251))
    page = np.full((page_height, page_width, 3), page_tone, dtype=np.uint8)
    inset_width = int(rng.integers(round(page_width * 0.45), round(page_width * 0.69)))
    inset_height = int(rng.integers(round(page_height * 0.43), round(page_height * 0.67)))
    inset = _fit_image(image, inset_width, inset_height)
    maximum_top = max(1, page_height - inset_height - round(page_height * 0.08))
    maximum_left = max(1, page_width - inset_width - round(page_width * 0.08))
    inset_top = int(rng.integers(round(page_height * 0.10), maximum_top + 1))
    inset_left = int(rng.integers(round(page_width * 0.08), maximum_left + 1))
    page[
        inset_top : inset_top + inset_height,
        inset_left : inset_left + inset_width,
    ] = inset

    margin_x = int(rng.integers(max(1, round(width * 0.07)), max(2, round(width * 0.17))))
    margin_y = int(rng.integers(max(1, round(height * 0.06)), max(2, round(height * 0.18))))
    jitter_x = int(rng.integers(0, max(1, round(width * 0.06))))
    jitter_y = int(rng.integers(0, max(1, round(height * 0.06))))
    source_quad = np.float32(
        [[0, 0], [page_width - 1, 0], [page_width - 1, page_height - 1], [0, page_height - 1]]
    )
    destination_quad = np.float32(
        [
            [margin_x + jitter_x, margin_y],
            [width - margin_x, margin_y + jitter_y],
            [width - margin_x - jitter_x, height - margin_y],
            [margin_x, height - margin_y - jitter_y],
        ]
    )
    transform = cv2.getPerspectiveTransform(source_quad, destination_quad)
    warped_page = cv2.warpPerspective(page, transform, (width, height))
    page_mask = cv2.warpPerspective(
        np.full((page_height, page_width), 255, dtype=np.uint8),
        transform,
        (width, height),
    )
    output = background.copy()
    output[page_mask > 0] = warped_page[page_mask > 0]

    contrast = float(rng.uniform(0.82, 1.12))
    brightness = float(rng.uniform(-18, 18))
    output = np.clip(output.astype(np.float32) * contrast + brightness, 0, 255).astype(
        np.uint8
    )
    downscale = float(rng.uniform(0.55, 0.9))
    reduced = cv2.resize(
        output,
        (max(1, round(width * downscale)), max(1, round(height * downscale))),
        interpolation=cv2.INTER_AREA,
    )
    output = cv2.resize(reduced, (width, height), interpolation=cv2.INTER_LINEAR)
    if rng.random() < 0.75:
        output = cv2.GaussianBlur(output, (3, 3), float(rng.uniform(0.25, 1.0)))
    quality = int(rng.integers(minimum_jpeg_quality, maximum_jpeg_quality + 1))
    success, encoded = cv2.imencode(".jpg", output, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not success:
        raise RuntimeError("could not encode printed-page view")
    decoded = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if not cv2.imwrite(str(destination), decoded, [cv2.IMWRITE_JPEG_QUALITY, 95]):
        raise RuntimeError(f"could not write printed-page view: {destination}")


def _parent_id(path: Path) -> str:
    return path.stem.split("--", 1)[0]


def build_hardening_datasets(
    *,
    source_root: Path,
    output_root: Path,
    class_directories: Sequence[str],
    target_train_images_per_class: int,
    printed_page_labels: Sequence[str],
    variants: Sequence[str],
    seed: int,
    printed_page: Mapping[str, Any],
) -> list[dict[str, str]]:
    """Build deterministic balanced variants without changing source splits."""
    if output_root.exists():
        raise FileExistsError(output_root)
    if tuple(directory.split("_", 1)[1] for directory in class_directories) != INTERNAL_LABELS:
        raise ValueError("class directory order is not canonical")
    if set(printed_page_labels) - set(INTERNAL_LABELS):
        raise ValueError("printed-page labels are not canonical")
    if set(variants) != {"balanced_oneview", "balanced_print"}:
        raise ValueError("expected balanced_oneview and balanced_print variants")
    rows: list[dict[str, str]] = []
    for variant in variants:
        for split in ("train", "val", "val_cal"):
            for class_directory, label in zip(class_directories, INTERNAL_LABELS):
                source_directory = source_root / split / class_directory
                sources = sorted(path for path in source_directory.iterdir() if path.is_file())
                if not sources:
                    raise ValueError(f"empty source class: {source_directory}")
                destination_directory = output_root / variant / split / class_directory
                destination_directory.mkdir(parents=True, exist_ok=False)
                if split != "train":
                    selected = [(source, "base", index) for index, source in enumerate(sources)]
                elif variant == "balanced_print" and label in printed_page_labels:
                    if len(sources) * 2 > target_train_images_per_class:
                        raise ValueError("target count is too small for base plus printed views")
                    selected = [(source, "base", index) for index, source in enumerate(sources)]
                    selected.extend(
                        (source, "print", index) for index, source in enumerate(sources)
                    )
                    repeats_needed = target_train_images_per_class - len(selected)
                    ordered = _ordered(sources, key=f"{seed}:{variant}:{label}:repeat")
                    selected.extend(
                        (ordered[index % len(ordered)], "repeat", index)
                        for index in range(repeats_needed)
                    )
                else:
                    if len(sources) > target_train_images_per_class:
                        raise ValueError("target count cannot drop source parents")
                    selected = [(source, "base", index) for index, source in enumerate(sources)]
                    repeats_needed = target_train_images_per_class - len(sources)
                    ordered = _ordered(sources, key=f"{seed}:{variant}:{label}:repeat")
                    selected.extend(
                        (ordered[index % len(ordered)], "repeat", index)
                        for index in range(repeats_needed)
                    )
                kind_counts: Counter[str] = Counter()
                for source, kind, ordinal in selected:
                    kind_counts[kind] += 1
                    parent_id = _parent_id(source)
                    suffix = source.suffix.casefold() if kind != "print" else ".jpg"
                    output_name = f"{parent_id}--{kind}-{kind_counts[kind]:04d}{suffix}"
                    destination = destination_directory / output_name
                    if kind == "print":
                        render_printed_page(
                            source,
                            destination,
                            seed_key=f"{seed}:{variant}:{label}:{parent_id}:{ordinal}",
                            **printed_page,
                        )
                    else:
                        _link_or_copy(source, destination)
                    rows.append(
                        {
                            "variant": variant,
                            "split": split,
                            "label": label,
                            "class_directory": class_directory,
                            "parent_image_id": parent_id,
                            "view_kind": kind,
                            "source_relative_path": source.relative_to(source_root).as_posix(),
                            "output_relative_path": destination.relative_to(output_root).as_posix(),
                            "output_sha256": sha256_file(destination),
                        }
                    )
    manifest = output_root / "manifest.csv"
    with manifest.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows
