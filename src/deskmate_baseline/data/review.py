"""Fail-closed human-review audit before any Baseline split can freeze."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ..domain.contracts import INTERNAL_LABELS, REPORTABLE_LABELS


FINAL_DECISIONS = {"accepted", "rejected"}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def audit_review_queue(
    *,
    manifest_path: Path,
    queue_path: Path,
    second_reviewer_required_for: set[str],
    release_floor_total: int,
    release_floor_per_class: int,
    preferred_per_class: int,
    not_target_floor: int,
) -> dict[str, Any]:
    manifest_rows = _read_csv(manifest_path)
    candidate_rows = {
        row["image_id"]: row
        for row in manifest_rows
        if row["review_status"] == "quarantine"
    }
    queue_rows = _read_csv(queue_path)
    errors: list[dict[str, str]] = []
    seen: set[str] = set()
    decisions: dict[str, str] = {}
    accepted_rows: list[dict[str, str]] = []

    for row in queue_rows:
        image_id = row.get("image_id", "")
        if image_id in seen:
            errors.append({"image_id": image_id, "code": "duplicate_queue_id"})
            continue
        seen.add(image_id)
        candidate = candidate_rows.get(image_id)
        if candidate is None:
            errors.append({"image_id": image_id, "code": "unknown_or_rejected_candidate"})
            continue
        decision = row.get("decision", "").casefold() or "pending"
        if decision not in FINAL_DECISIONS | {"pending"}:
            errors.append({"image_id": image_id, "code": "invalid_decision"})
            continue
        decisions[image_id] = decision
        if decision in FINAL_DECISIONS and not row.get("reviewer"):
            errors.append({"image_id": image_id, "code": "missing_reviewer"})
        label = candidate["label"]
        if label in second_reviewer_required_for and decision in FINAL_DECISIONS:
            second_decision = row.get("second_decision", "").casefold()
            if second_decision != decision:
                errors.append({"image_id": image_id, "code": "second_review_disagrees_or_missing"})
            if not row.get("second_reviewer"):
                errors.append({"image_id": image_id, "code": "missing_second_reviewer"})
            elif row.get("second_reviewer", "").casefold() == row.get(
                "reviewer", ""
            ).casefold():
                errors.append({"image_id": image_id, "code": "reviewers_must_be_distinct"})
        if decision == "accepted":
            accepted_rows.append(candidate)

    missing_queue_ids = sorted(set(candidate_rows) - seen)
    for image_id in missing_queue_ids:
        errors.append({"image_id": image_id, "code": "missing_queue_row"})

    accepted_by_cluster: dict[str, list[str]] = defaultdict(list)
    for row in accepted_rows:
        if row["duplicate_cluster_id"]:
            accepted_by_cluster[row["duplicate_cluster_id"]].append(row["image_id"])
    for cluster_id, image_ids in accepted_by_cluster.items():
        if len(image_ids) > 1:
            errors.append(
                {
                    "image_id": ",".join(sorted(image_ids)),
                    "code": f"multiple_accepted_in_cluster:{cluster_id}",
                }
            )

    accepted_counts = Counter(row["label"] for row in accepted_rows)
    decision_counts = Counter(decisions.values())
    target_total = sum(accepted_counts[label] for label in REPORTABLE_LABELS)
    all_reviewed = (
        len(decisions) == len(candidate_rows)
        and decision_counts["pending"] == 0
        and not missing_queue_ids
    )
    release_floor_ready = target_total >= release_floor_total and all(
        accepted_counts[label] >= release_floor_per_class for label in REPORTABLE_LABELS
    )
    preferred_ready = all(
        accepted_counts[label] >= preferred_per_class for label in REPORTABLE_LABELS
    )
    not_target_ready = accepted_counts["not_target"] >= not_target_floor
    return {
        "schema_version": 1,
        "candidate_rows": len(candidate_rows),
        "queue_rows": len(queue_rows),
        "decision_counts": {
            "accepted": decision_counts["accepted"],
            "rejected": decision_counts["rejected"],
            "pending": len(candidate_rows)
            - decision_counts["accepted"]
            - decision_counts["rejected"],
        },
        "accepted_unique": {label: accepted_counts[label] for label in INTERNAL_LABELS},
        "accepted_target_total": target_total,
        "gap_to_preferred": {
            label: max(0, preferred_per_class - accepted_counts[label])
            for label in REPORTABLE_LABELS
        },
        "all_reviewed": all_reviewed,
        "release_floor_ready": release_floor_ready,
        "preferred_ready": preferred_ready,
        "not_target_floor_ready": not_target_ready,
        "errors": errors,
        "error_count": len(errors),
        "ready_to_freeze_split": all_reviewed
        and release_floor_ready
        and not_target_ready
        and not errors,
    }
