from __future__ import annotations

import hashlib
import io
from pathlib import Path

from PIL import Image

from deskmate_baseline.data.dataset_prep import (
    coverage_decision,
    dhash64,
    hamming_distance,
    prepare_candidate_rows,
)
from deskmate_baseline.domain.manifest import MANIFEST_FIELDS


def image_bytes(color: tuple[int, int, int]) -> bytes:
    stream = io.BytesIO()
    Image.new("RGB", (200, 180), color).save(stream, format="PNG")
    return stream.getvalue()


def row(image_id: str, label: str, data: bytes) -> dict[str, str]:
    values = {field: "" for field in MANIFEST_FIELDS}
    values.update(
        {
            "image_id": image_id,
            "label": label,
            "source_kind": "wikimedia_commons",
            "source_dataset": "fixture",
            "source_page_url": "https://example.test/page",
            "original_url": "https://example.test/image.png",
            "author": "fixture",
            "license_name": "CC0",
            "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
            "downloaded_at": "2026-07-14T00:00:00+08:00",
            "source_group_id": image_id,
            "exact_sha256": hashlib.sha256(data).hexdigest(),
            "width": "200",
            "height": "180",
            "review_status": "quarantine",
            "split": "staging",
        }
    )
    return values


def write_fixture(root: Path, image_id: str, label: str, data: bytes) -> None:
    path = root / "commons" / label / f"{image_id}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def test_dhash_is_stable_and_64_bit() -> None:
    left = dhash64(image_bytes((10, 20, 30)))
    right = dhash64(image_bytes((10, 20, 30)))
    assert left == right
    assert len(left) == 16
    assert hamming_distance(left, right) == 0


def test_prepare_rows_rejects_exact_duplicate_without_accepting(tmp_path: Path) -> None:
    data = image_bytes((20, 40, 60))
    rows = [row("commons-1", "ragdoll", data), row("commons-2", "ragdoll", data)]
    for item in rows:
        write_fixture(tmp_path, item["image_id"], item["label"], data)
    prepared, report = prepare_candidate_rows(
        rows,
        artifact_root=tmp_path,
        minimum_width=160,
        minimum_height=160,
        near_duplicate_hamming_distance=4,
    )
    assert [item["review_status"] for item in prepared] == ["quarantine", "rejected"]
    assert report["candidate_unique"]["ragdoll"] == 1
    assert report["accepted_unique"]["ragdoll"] == 0
    assert len(report["exact_duplicate_clusters"]) == 1
    assert all(len(item["perceptual_hash"]) == 16 for item in prepared)


def test_prepare_rows_rejects_cross_label_exact_conflict(tmp_path: Path) -> None:
    data = image_bytes((90, 80, 70))
    rows = [row("commons-3", "ragdoll", data), row("commons-4", "persian", data)]
    for item in rows:
        write_fixture(tmp_path, item["image_id"], item["label"], data)
    prepared, report = prepare_candidate_rows(
        rows,
        artifact_root=tmp_path,
        minimum_width=160,
        minimum_height=160,
        near_duplicate_hamming_distance=4,
    )
    assert all(item["review_status"] == "rejected" for item in prepared)
    assert len(report["exact_label_conflicts"]) == 1


def test_prepare_rows_rejects_same_original_url_after_reencoding(tmp_path: Path) -> None:
    first = image_bytes((10, 30, 50))
    second = image_bytes((11, 31, 51))
    rows = [row("commons-5", "pallas", first), row("commons-6", "pallas", second)]
    rows[0]["original_url"] = "http://images.example.test/photo.jpg?size=medium"
    rows[1]["original_url"] = "https://images.example.test/photo.jpg"
    for item, data in zip(rows, (first, second)):
        write_fixture(tmp_path, item["image_id"], item["label"], data)
    prepared, report = prepare_candidate_rows(
        rows,
        artifact_root=tmp_path,
        minimum_width=160,
        minimum_height=160,
        near_duplicate_hamming_distance=4,
    )
    assert [item["review_status"] for item in prepared] == ["quarantine", "rejected"]
    assert len(report["url_duplicate_clusters"]) == 1


def test_candidate_coverage_never_authorizes_selenium_or_acceptance() -> None:
    preparation = {
        "candidate_unique": {
            "ragdoll": 400,
            "singapura": 400,
            "persian": 400,
            "sphynx": 400,
            "pallas": 400,
            "not_target": 300,
        }
    }
    decision = coverage_decision(
        preparation,
        release_floor_total=1200,
        release_floor_per_class=220,
        preferred_per_class=400,
        not_target_floor=300,
    )
    assert decision["candidate_release_floor_ready"]
    assert decision["candidate_not_target_floor_ready"]
    assert not decision["accepted_release_floor_ready"]
    assert not decision["selenium_authorized"]


def test_original_url_normalization_keeps_archive_member_identity() -> None:
    from deskmate_baseline.data.dataset_prep import normalize_original_url

    first = normalize_original_url("https://example.test/images.tar.gz#images/Persian_1.jpg")
    second = normalize_original_url("https://example.test/images.tar.gz#images/Persian_2.jpg")
    assert first != second
