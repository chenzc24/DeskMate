from __future__ import annotations

import csv
from pathlib import Path

from deskmate_baseline.manifest import MANIFEST_FIELDS, audit_manifest


def row(**overrides: str) -> dict[str, str]:
    values = {
        "image_id": "img-1",
        "label": "ragdoll",
        "source_kind": "official_dataset",
        "source_dataset": "fixture",
        "source_page_url": "https://example.test/page/1",
        "original_url": "https://example.test/image/1.jpg",
        "author": "fixture-author",
        "license_name": "CC-BY-4.0",
        "license_url": "https://example.test/license",
        "downloaded_at": "2026-07-14T12:00:00+08:00",
        "source_group_id": "source-group-1",
        "exact_sha256": "a" * 64,
        "perceptual_hash": "b" * 16,
        "width": "640",
        "height": "480",
        "review_status": "accepted",
        "reviewer": "reviewer-1",
        "duplicate_cluster_id": "cluster-1",
        "split": "staging",
    }
    values.update(overrides)
    return values


def write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def issue_codes(report: dict[str, object]) -> set[str]:
    return {issue["code"] for issue in report["issues"]}


def test_valid_staging_manifest_is_auditable_and_computes_gap_fill(tmp_path: Path) -> None:
    path = tmp_path / "valid.csv"
    write_manifest(path, [row()])
    report = audit_manifest(path)
    assert report["ok"]
    assert report["accepted_unique"]["ragdoll"] == 1
    ragdoll = report["selenium_go_no_go"]["ragdoll"]
    assert ragdoll["gap_to_target"] == 399
    assert ragdoll["candidate_buffer"] == 499
    assert ragdoll["enable_targeted_gap_fill"]
    assert report["not_target_gap_to_floor"] == 300


def test_invalid_label_and_missing_license_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "invalid.csv"
    write_manifest(path, [row(label="unknown", license_name="", license_url="")])
    report = audit_manifest(path)
    assert not report["ok"]
    assert {"invalid_label", "missing_license_name", "missing_license_url"} <= issue_codes(report)


def test_exact_duplicate_and_group_leakage_are_errors(tmp_path: Path) -> None:
    path = tmp_path / "leak.csv"
    write_manifest(
        path,
        [
            row(split="train"),
            row(
                image_id="img-2",
                original_url="https://example.test/image/2.jpg",
                split="val_select",
            ),
        ],
    )
    report = audit_manifest(path)
    assert not report["ok"]
    assert {
        "exact_duplicate",
        "cross_split_exact_duplicate",
        "cross_split_source_group",
        "cross_split_duplicate_cluster",
    } <= issue_codes(report)


def test_empty_template_is_warning_not_error() -> None:
    path = Path("data/manifests/source_manifest.template.csv")
    report = audit_manifest(path)
    assert report["ok"]
    assert report["warning_count"] == 1
    assert "empty_manifest" in issue_codes(report)


def test_quarantine_pilot_requires_provenance_but_not_review_or_phash(tmp_path: Path) -> None:
    path = tmp_path / "pilot.csv"
    write_manifest(
        path,
        [row(review_status="quarantine", reviewer="", perceptual_hash="")],
    )
    report = audit_manifest(path)
    assert report["ok"]
    assert report["quarantine_rows"] == 1
    assert report["candidate_unique"]["ragdoll"] == 1
    assert report["accepted_unique"]["ragdoll"] == 0

    write_manifest(
        path,
        [
            row(
                review_status="quarantine",
                reviewer="",
                perceptual_hash="",
                license_name="",
            )
        ],
    )
    report = audit_manifest(path)
    assert not report["ok"]
    assert "missing_license_name" in issue_codes(report)
