from __future__ import annotations

import csv
from pathlib import Path

from deskmate_baseline.manifest import MANIFEST_FIELDS
from deskmate_baseline.review import audit_review_queue


QUEUE_FIELDS = [
    "image_id",
    "label",
    "decision",
    "reviewer",
    "second_decision",
    "second_reviewer",
]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def manifest_row(image_id: str, label: str, cluster: str = "") -> dict[str, str]:
    row = {field: "" for field in MANIFEST_FIELDS}
    row.update(
        {
            "image_id": image_id,
            "label": label,
            "review_status": "quarantine",
            "duplicate_cluster_id": cluster,
        }
    )
    return row


def run_audit(tmp_path: Path, queue_rows: list[dict[str, str]], manifest_rows=None):
    manifest_rows = manifest_rows or [manifest_row("image-1", "singapura")]
    manifest = tmp_path / "manifest.csv"
    queue = tmp_path / "queue.csv"
    write_csv(manifest, list(MANIFEST_FIELDS), manifest_rows)
    write_csv(queue, QUEUE_FIELDS, queue_rows)
    return audit_review_queue(
        manifest_path=manifest,
        queue_path=queue,
        second_reviewer_required_for={"singapura"},
        release_floor_total=1,
        release_floor_per_class=0,
        preferred_per_class=1,
        not_target_floor=0,
    )


def test_pending_review_is_valid_but_not_ready(tmp_path: Path) -> None:
    report = run_audit(
        tmp_path,
        [
            {
                "image_id": "image-1",
                "label": "singapura",
                "decision": "",
                "reviewer": "",
                "second_decision": "",
                "second_reviewer": "",
            }
        ],
    )
    assert report["error_count"] == 0
    assert report["decision_counts"]["pending"] == 1
    assert not report["ready_to_freeze_split"]


def test_easy_confusion_class_requires_distinct_agreeing_reviewers(tmp_path: Path) -> None:
    report = run_audit(
        tmp_path,
        [
            {
                "image_id": "image-1",
                "label": "singapura",
                "decision": "accepted",
                "reviewer": "reviewer-a",
                "second_decision": "",
                "second_reviewer": "",
            }
        ],
    )
    codes = {item["code"] for item in report["errors"]}
    assert "second_review_disagrees_or_missing" in codes
    assert "missing_second_reviewer" in codes


def test_two_images_in_one_duplicate_cluster_cannot_both_be_accepted(tmp_path: Path) -> None:
    rows = [
        manifest_row("image-1", "ragdoll", "near-1"),
        manifest_row("image-2", "ragdoll", "near-1"),
    ]
    queue = [
        {
            "image_id": image_id,
            "label": "ragdoll",
            "decision": "accepted",
            "reviewer": "reviewer-a",
            "second_decision": "",
            "second_reviewer": "",
        }
        for image_id in ("image-1", "image-2")
    ]
    report = run_audit(tmp_path, queue, rows)
    assert any(
        item["code"].startswith("multiple_accepted_in_cluster")
        for item in report["errors"]
    )
