from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from PIL import Image

from scripts.data.build_five_breed_detector_dataset import build_dataset


BASE_FIELDS = [
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
]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def make_pair(root: Path, split: str, sample_id: str, *, positive: bool) -> tuple[Path, Path]:
    image = root / "images" / split / f"{sample_id}.jpg"
    label = root / "labels" / split / f"{sample_id}.txt"
    image.parent.mkdir(parents=True, exist_ok=True)
    label.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (80, 60), (120, 80, 40)).save(image)
    label.write_text("0 0.500000 0.500000 0.500000 0.500000\n" if positive else "")
    return image, label


def test_build_dataset_joins_sources_and_hashes_every_item(tmp_path: Path) -> None:
    base = tmp_path / "base"
    sphynx_image, sphynx_label = make_pair(base, "train", "sphynx-1", positive=True)
    negative_image, negative_label = make_pair(base, "train", "negative-1", positive=False)
    base_rows = []
    for sample_id, breed, image, label, boxes in (
        ("sphynx-1", "sphynx", sphynx_image, sphynx_label, 1),
        ("negative-1", "not_target", negative_image, negative_label, 0),
    ):
        base_rows.append(
            {
                "sample_id": sample_id,
                "breed": breed,
                "split": "train",
                "source_image": str(image),
                "source_label": str(label),
                "output_image": str(image),
                "output_label": str(label),
                "width": 80,
                "height": 60,
                "box_count": boxes,
                "image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
                "label_sha256": hashlib.sha256(label.read_bytes()).hexdigest(),
            }
        )
    write_csv(base / "manifest.csv", BASE_FIELDS, base_rows)

    returned = tmp_path / "returned"
    ragdoll_image, ragdoll_label = make_pair(returned, "train", "ragdoll-1", positive=True)
    returned_rows = [
        {
            "relative_path": "0_ragdoll/ragdoll-1.jpg",
            "export_image": "images/train/ragdoll-1.jpg",
            "export_label": "labels/train/ragdoll-1.txt",
            "split": "train",
            "breed_group": "0_ragdoll",
            "box_count": 1,
            "box_sources": "manual",
            "quality_flags": "",
        }
    ]
    write_csv(
        returned / "manifest.csv",
        list(returned_rows[0]),
        returned_rows,
    )
    selection = tmp_path / "selection.csv"
    write_csv(selection, ["source_sha256"], [{"source_sha256": "0" * 64}])

    output = tmp_path / "output"
    report = build_dataset(
        project_root=tmp_path,
        bd05_base=base,
        three_breed=returned,
        selection_manifest=selection,
        output=output,
    )

    assert report["totals"] == {
        "images": 3,
        "boxes": 2,
        "train_images": 3,
        "val_images": 0,
        "test_images": 0,
    }
    assert report["diagnostic_24_exact_overlap"] == []
    rows = list(csv.DictReader((output / "manifest.csv").open(encoding="utf-8")))
    assert {row["breed"] for row in rows} == {"sphynx", "ragdoll", "not_target"}
    assert all(len(row["image_sha256"]) == 64 for row in rows)
    assert all(len(row["label_sha256"]) == 64 for row in rows)
    assert (output / "images/train/ragdoll-1.jpg").read_bytes() == ragdoll_image.read_bytes()
    assert (output / "labels/train/ragdoll-1.txt").read_bytes() == ragdoll_label.read_bytes()


def test_build_dataset_rejects_out_of_bounds_box(tmp_path: Path) -> None:
    base = tmp_path / "base"
    image, label = make_pair(base, "train", "sphynx-1", positive=True)
    label.write_text("0 0.95 0.5 0.2 0.5\n", encoding="utf-8")
    write_csv(
        base / "manifest.csv",
        BASE_FIELDS,
        [
            {
                "sample_id": "sphynx-1",
                "breed": "sphynx",
                "split": "train",
                "source_image": str(image),
                "source_label": str(label),
                "output_image": str(image),
                "output_label": str(label),
                "width": 80,
                "height": 60,
                "box_count": 1,
                "image_sha256": "",
                "label_sha256": "",
            }
        ],
    )
    returned = tmp_path / "returned"
    returned.mkdir()
    write_csv(
        returned / "manifest.csv",
        ["relative_path", "export_image", "export_label", "split", "breed_group", "box_count", "box_sources", "quality_flags"],
        [],
    )
    selection = tmp_path / "selection.csv"
    write_csv(selection, ["source_sha256"], [])

    try:
        build_dataset(
            project_root=tmp_path,
            bd05_base=base,
            three_breed=returned,
            selection_manifest=selection,
            output=tmp_path / "output",
        )
    except ValueError as exc:
        assert "box ends outside image" in str(exc)
    else:
        raise AssertionError("out-of-bounds box was accepted")
