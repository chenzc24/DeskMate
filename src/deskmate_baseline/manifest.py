"""Audit source manifests before any image can enter a frozen split."""

from __future__ import annotations

import csv
import math
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .contracts import INTERNAL_LABELS, REPORTABLE_LABELS


MANIFEST_FIELDS: tuple[str, ...] = (
    "image_id",
    "label",
    "source_kind",
    "source_dataset",
    "source_page_url",
    "original_url",
    "author",
    "license_name",
    "license_url",
    "downloaded_at",
    "source_group_id",
    "exact_sha256",
    "perceptual_hash",
    "width",
    "height",
    "review_status",
    "reviewer",
    "duplicate_cluster_id",
    "split",
)
ALLOWED_REVIEW_STATUS = {"pending", "accepted", "rejected", "quarantine"}
ALLOWED_SPLITS = {"", "staging", "train", "val_select", "val_cal"}
HEX_64 = re.compile(r"^[0-9a-fA-F]{64}$")
HEX_PHASH = re.compile(r"^[0-9a-fA-F]{16,64}$")


@dataclass(frozen=True, slots=True)
class ManifestIssue:
    severity: str
    code: str
    row: int | None
    message: str


def _issue(
    issues: list[ManifestIssue],
    severity: str,
    code: str,
    row: int | None,
    message: str,
) -> None:
    issues.append(ManifestIssue(severity, code, row, message))


def _group_splits(
    rows: Iterable[tuple[int, dict[str, str]]], field: str
) -> dict[str, set[str]]:
    groups: dict[str, set[str]] = defaultdict(set)
    for _, row in rows:
        value = row[field]
        split = row["split"]
        if value and split in {"train", "val_select", "val_cal"}:
            groups[value].add(split)
    return groups


def audit_manifest(
    path: str | Path,
    *,
    target_per_class: int = 400,
    review_buffer: float = 1.25,
    not_target_floor: int = 300,
) -> dict[str, object]:
    manifest_path = Path(path)
    issues: list[ManifestIssue] = []
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = tuple(reader.fieldnames or ())
        missing_headers = [field for field in MANIFEST_FIELDS if field not in headers]
        extra_headers = [field for field in headers if field not in MANIFEST_FIELDS]
        if missing_headers:
            _issue(
                issues,
                "error",
                "missing_headers",
                None,
                f"missing headers: {', '.join(missing_headers)}",
            )
        if extra_headers:
            _issue(
                issues,
                "warning",
                "extra_headers",
                None,
                f"extra headers: {', '.join(extra_headers)}",
            )
        rows = [
            (row_number, {field: (row.get(field) or "").strip() for field in MANIFEST_FIELDS})
            for row_number, row in enumerate(reader, start=2)
        ]

    seen_ids: dict[str, int] = {}
    accepted_rows: list[tuple[int, dict[str, str]]] = []
    candidate_rows: list[tuple[int, dict[str, str]]] = []
    exact_hash_rows: dict[str, list[tuple[int, dict[str, str]]]] = defaultdict(list)

    for row_number, row in rows:
        image_id = row["image_id"]
        if not image_id:
            _issue(issues, "error", "missing_image_id", row_number, "image_id is required")
        elif image_id in seen_ids:
            _issue(
                issues,
                "error",
                "duplicate_image_id",
                row_number,
                f"image_id first appeared on row {seen_ids[image_id]}",
            )
        else:
            seen_ids[image_id] = row_number

        if row["label"] not in INTERNAL_LABELS:
            _issue(
                issues,
                "error",
                "invalid_label",
                row_number,
                f"label must be one of: {', '.join(INTERNAL_LABELS)}",
            )
        if row["review_status"] not in ALLOWED_REVIEW_STATUS:
            _issue(
                issues,
                "error",
                "invalid_review_status",
                row_number,
                f"invalid review_status: {row['review_status']}",
            )
        if row["split"] not in ALLOWED_SPLITS:
            _issue(
                issues,
                "error",
                "invalid_split",
                row_number,
                f"invalid split: {row['split']}",
            )

        if row["review_status"] not in {"accepted", "quarantine"}:
            continue
        candidate_rows.append((row_number, row))
        required_values = (
            "source_kind",
            "source_dataset",
            "source_page_url",
            "original_url",
            "license_name",
            "license_url",
            "downloaded_at",
            "source_group_id",
            "split",
        )
        for field in required_values:
            if not row[field]:
                _issue(
                    issues,
                    "error",
                    f"missing_{field}",
                    row_number,
                    f"accepted/quarantine row requires {field}",
                )
        if not HEX_64.fullmatch(row["exact_sha256"]):
            _issue(
                issues,
                "error",
                "invalid_sha256",
                row_number,
                "accepted row requires a 64-character hexadecimal SHA-256",
            )
        else:
            exact_hash_rows[row["exact_sha256"].lower()].append((row_number, row))
        if row["review_status"] == "accepted" and not row["reviewer"]:
            _issue(
                issues,
                "error",
                "missing_reviewer",
                row_number,
                "accepted row requires reviewer",
            )
        if row["review_status"] == "accepted" and not HEX_PHASH.fullmatch(
            row["perceptual_hash"]
        ):
            _issue(
                issues,
                "error",
                "invalid_perceptual_hash",
                row_number,
                "accepted row requires a 16-64 character hexadecimal perceptual hash",
            )
        for field in ("width", "height"):
            try:
                if int(row[field]) <= 0:
                    raise ValueError
            except ValueError:
                _issue(
                    issues,
                    "error",
                    f"invalid_{field}",
                    row_number,
                    f"accepted row requires a positive integer {field}",
                )
        if row["review_status"] == "accepted":
            accepted_rows.append((row_number, row))

    for exact_hash, duplicate_rows in exact_hash_rows.items():
        if len(duplicate_rows) <= 1:
            continue
        row_numbers = [row_number for row_number, _ in duplicate_rows]
        any_accepted = any(row["review_status"] == "accepted" for _, row in duplicate_rows)
        _issue(
            issues,
            "error" if any_accepted else "warning",
            "exact_duplicate" if any_accepted else "candidate_exact_duplicate",
            row_numbers[-1],
            f"SHA-256 {exact_hash} appears on rows {row_numbers}",
        )
        splits = {row["split"] for _, row in duplicate_rows}
        if any_accepted and len(splits) > 1:
            _issue(
                issues,
                "error",
                "cross_split_exact_duplicate",
                row_numbers[-1],
                f"exact duplicate crosses splits: {sorted(splits)}",
            )

    for field, code in (
        ("source_group_id", "cross_split_source_group"),
        ("duplicate_cluster_id", "cross_split_duplicate_cluster"),
    ):
        for group_id, splits in _group_splits(accepted_rows, field).items():
            if len(splits) > 1:
                _issue(
                    issues,
                    "error",
                    code,
                    None,
                    f"{field} {group_id} crosses splits: {sorted(splits)}",
                )

    unique_hashes_by_label: dict[str, set[str]] = defaultdict(set)
    for _, row in accepted_rows:
        if HEX_64.fullmatch(row["exact_sha256"]):
            unique_hashes_by_label[row["label"]].add(row["exact_sha256"].lower())
    accepted_unique = {
        label: len(unique_hashes_by_label[label]) for label in INTERNAL_LABELS
    }
    candidate_hashes_by_label: dict[str, set[str]] = defaultdict(set)
    for _, row in candidate_rows:
        if HEX_64.fullmatch(row["exact_sha256"]):
            candidate_hashes_by_label[row["label"]].add(row["exact_sha256"].lower())
    candidate_unique = {
        label: len(candidate_hashes_by_label[label]) for label in INTERNAL_LABELS
    }
    selenium_go_no_go = {}
    for label in REPORTABLE_LABELS:
        gap = max(0, target_per_class - accepted_unique[label])
        selenium_go_no_go[label] = {
            "accepted_unique": accepted_unique[label],
            "gap_to_target": gap,
            "candidate_buffer": math.ceil(gap * review_buffer),
            "enable_targeted_gap_fill": gap > 0,
        }

    severity_counts = Counter(issue.severity for issue in issues)
    if not rows:
        _issue(issues, "warning", "empty_manifest", None, "manifest contains no rows")
        severity_counts["warning"] += 1

    return {
        "schema_version": 1,
        "manifest": str(manifest_path),
        "rows": len(rows),
        "accepted_rows": len(accepted_rows),
        "quarantine_rows": sum(
            row["review_status"] == "quarantine" for _, row in candidate_rows
        ),
        "accepted_unique": accepted_unique,
        "candidate_unique": candidate_unique,
        "not_target_gap_to_floor": max(0, not_target_floor - accepted_unique["not_target"]),
        "selenium_go_no_go": selenium_go_no_go,
        "issues": [asdict(issue) for issue in issues],
        "error_count": severity_counts["error"],
        "warning_count": severity_counts["warning"],
        "ok": severity_counts["error"] == 0,
    }
