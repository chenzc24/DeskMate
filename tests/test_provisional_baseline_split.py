from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from PIL import Image

from scripts.build_provisional_baseline_split import (
    INTERNAL_LABELS,
    MANIFEST_FIELDS,
    build_dataset,
    grouped_components,
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def image(path: Path, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (180, 180), color).save(path, format="JPEG")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fixture(tmp_path: Path) -> tuple[Path, Path]:
    target_root = tmp_path / "target"
    target_manifest = target_root / "intake_manifest.csv"
    target_fields = [
        "intake_id", "label", "materialized_relative_path", "exact_sha256",
        "source_group_id", "near_cluster_id", "technical_status",
        "screening_status", "provenance_status",
    ]
    target_rows = []
    for label_index, label in enumerate(INTERNAL_LABELS[:-1]):
        for index in range(4):
            relative = Path("clean_candidates") / label / f"{label}-{index}.jpg"
            path = target_root / relative
            image(path, (10 + label_index * 30, 20 + index * 20, 30 + label_index + index))
            target_rows.append(
                {
                    "intake_id": f"{label}-{index}",
                    "label": label,
                    "materialized_relative_path": relative.as_posix(),
                    "exact_sha256": sha(path),
                    "source_group_id": f"{label}-pair" if index < 2 else "",
                    "near_cluster_id": "",
                    "technical_status": "candidate",
                    "screening_status": "human_screened_claimed",
                    "provenance_status": "missing",
                }
            )
    write_csv(target_manifest, target_fields, target_rows)

    negative_root = tmp_path / "negative"
    negative_manifest = negative_root / "source_manifest.csv"
    negative_fields = [
        "image_id", "label", "review_status", "source_kind", "source_group_id",
        "duplicate_cluster_id", "exact_sha256",
    ]
    negative_rows = []
    for index in range(4):
        image_id = f"negative-{index}"
        path = negative_root / "commons" / "not_target" / f"{image_id}.jpg"
        image(path, (150, 20 + index * 25, 40))
        negative_rows.append(
            {
                "image_id": image_id,
                "label": "not_target",
                "review_status": "quarantine",
                "source_kind": "wikimedia_commons",
                "source_group_id": "negative-pair" if index < 2 else "",
                "duplicate_cluster_id": "",
                "exact_sha256": sha(path),
            }
        )
    write_csv(negative_manifest, negative_fields, negative_rows)

    output = tmp_path / "output"
    config = tmp_path / "config.toml"
    config.write_text(
        f'''schema_version = 1
[paths]
target_manifest = "{target_manifest.as_posix()}"
target_root = "{target_root.as_posix()}"
negative_manifest = "{negative_manifest.as_posix()}"
negative_root = "{negative_root.as_posix()}"
output_root = "{output.as_posix()}"
[selection]
target_status = "candidate"
negative_label = "not_target"
negative_status = "quarantine"
allow_pending_negative_review = true
defer_provenance_and_license = true
group_same_label_dhash_clusters = true
ignore_cross_label_dhash_only_clusters = true
[split]
seed = 20260715
train = 0.5
val_select = 0.25
val_cal = 0.25
[release_floor]
target_total = 20
target_per_class = 4
not_target = 4
[materialization]
method = "copy"
verify_sha256 = true
''',
        encoding="utf-8",
    )
    return config, output


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_builds_six_class_materialized_split(tmp_path: Path) -> None:
    config, output = fixture(tmp_path)
    report = build_dataset(config_path=config)
    assert report["provisional_training_data_ready"] is True
    assert report["official_gate_b1_ready"] is False
    assert report["rows"] == 24
    assert set(report["class_counts"]) == set(INTERNAL_LABELS)
    assert len(list((output / "yolo_classify").rglob("*.jpg"))) == 24
    rows = read_manifest(output / "provisional_split_manifest.csv")
    assert tuple(rows[0]) == MANIFEST_FIELDS
    for label in INTERNAL_LABELS:
        group_id = "negative-pair" if label == "not_target" else f"{label}-pair"
        pair = [row for row in rows if row["source_group_id"] == group_id]
        assert len({row["split"] for row in pair}) == 1


def test_no_materialization_is_deterministic(tmp_path: Path) -> None:
    config, output = fixture(tmp_path)
    second = tmp_path / "second"
    first_report = build_dataset(config_path=config, materialize_files=False)
    second_report = build_dataset(
        config_path=config, output_root=second, materialize_files=False
    )
    assert first_report == second_report
    assert (output / "provisional_split_manifest.csv").read_bytes() == (
        second / "provisional_split_manifest.csv"
    ).read_bytes()


def test_grouped_components_links_duplicate_groups() -> None:
    rows = [
        {
            "sample_id": "one", "source_group_id": "", "duplicate_group_id": "d1",
            "exact_sha256": "a" * 64,
        },
        {
            "sample_id": "two", "source_group_id": "", "duplicate_group_id": "d1",
            "exact_sha256": "b" * 64,
        },
        {
            "sample_id": "three", "source_group_id": "", "duplicate_group_id": "",
            "exact_sha256": "c" * 64,
        },
    ]
    assert sorted(len(group) for group in grouped_components(rows)) == [1, 2]
