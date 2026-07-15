from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pytest

from deskmate_baseline.contracts import INTERNAL_LABELS
from deskmate_baseline.manifest import MANIFEST_FIELDS
from deskmate_baseline.split import (
    CLASS_DIRS,
    GateB1NotReady,
    build_frozen_split,
    materialize_dataset_view,
)


QUEUE_FIELDS = (
    "image_id", "label", "source_kind", "source_dataset", "source_group_id",
    "duplicate_cluster_id", "batch", "decision", "reviewer", "second_decision",
    "second_reviewer", "notes",
)


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _fixture(tmp_path: Path, *, pending: bool = False):
    manifest_rows = []
    queue_rows = []
    for label in INTERNAL_LABELS:
        for index in range(12):
            image_id = f"{label}-{index:02d}"
            digest = hashlib.sha256(image_id.encode()).hexdigest()
            group = f"{label}-pair" if index < 2 else image_id
            manifest_rows.append({
                **{field: "" for field in MANIFEST_FIELDS},
                "image_id": image_id, "label": label, "source_kind": "wikimedia_commons",
                "source_dataset": "fixture", "source_page_url": "https://example.test/page",
                "original_url": "https://example.test/image", "license_name": "CC0",
                "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                "downloaded_at": "2026-07-15T00:00:00+08:00", "source_group_id": group,
                "exact_sha256": digest, "perceptual_hash": digest[:16], "width": "224",
                "height": "224", "review_status": "quarantine", "split": "staging",
            })
            needs_second = label in {"singapura", "pallas", "persian"}
            decision = "" if pending and index == 0 else "accepted"
            queue_rows.append({
                "image_id": image_id, "label": label, "source_kind": "wikimedia_commons",
                "source_dataset": "fixture", "source_group_id": group,
                "duplicate_cluster_id": "", "batch": f"{label}-001", "decision": decision,
                "reviewer": "alice" if decision else "", "second_decision": decision if needs_second else "",
                "second_reviewer": "bob" if needs_second and decision else "", "notes": "",
            })
    manifest = tmp_path / "manifest.csv"
    queue = tmp_path / "queue.csv"
    _write_csv(manifest, MANIFEST_FIELDS, manifest_rows)
    _write_csv(queue, QUEUE_FIELDS, queue_rows)
    return manifest, queue


def _build(manifest: Path, queue: Path):
    return build_frozen_split(
        manifest_path=manifest, queue_path=queue,
        second_reviewer_required_for={"singapura", "pallas", "persian"},
        release_floor_total=60, release_floor_per_class=10, preferred_per_class=12,
        not_target_floor=10, seed=20260714,
    )


def test_split_refuses_pending_review(tmp_path: Path) -> None:
    manifest, queue = _fixture(tmp_path, pending=True)
    with pytest.raises(GateB1NotReady) as exc:
        _build(manifest, queue)
    assert exc.value.report["decision_counts"]["pending"] == len(INTERNAL_LABELS)


def test_split_is_deterministic_and_keeps_groups_together(tmp_path: Path) -> None:
    manifest, queue = _fixture(tmp_path)
    first, first_report = _build(manifest, queue)
    second, second_report = _build(manifest, queue)
    assert first == second
    assert first_report == second_report
    assert tuple(first_report["class_order"]) == INTERNAL_LABELS
    for label in INTERNAL_LABELS:
        pair = [row for row in first if row["source_group_id"] == f"{label}-pair"]
        assert len({row["split"] for row in pair}) == 1
        assert sum(first_report["allocation"][label]["actual_counts"].values()) == 12


def test_split_refuses_same_second_reviewer(tmp_path: Path) -> None:
    manifest, queue = _fixture(tmp_path)
    rows = list(csv.DictReader(queue.open(encoding="utf-8")))
    row = next(item for item in rows if item["label"] == "pallas")
    row["second_reviewer"] = row["reviewer"].upper()
    _write_csv(queue, QUEUE_FIELDS, rows)
    with pytest.raises(GateB1NotReady) as exc:
        _build(manifest, queue)
    assert any(error["code"] == "reviewers_must_be_distinct" for error in exc.value.report["errors"])


def test_materialized_view_is_idempotent_and_uses_canonical_prefixes(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    payload = b"fixture-image"
    source = source_root / "commons" / "ragdoll" / "sample.jpg"
    source.parent.mkdir(parents=True)
    source.write_bytes(payload)
    row = {
        "image_id": "sample",
        "label": "ragdoll",
        "source_kind": "wikimedia_commons",
        "split": "train",
        "exact_sha256": hashlib.sha256(payload).hexdigest(),
    }
    output = tmp_path / "view"
    first = materialize_dataset_view(rows=[row], source_root=source_root, output_root=output)
    second = materialize_dataset_view(rows=[row], source_root=source_root, output_root=output)
    expected = output / "train" / CLASS_DIRS["ragdoll"] / "sample.jpg"
    assert expected.read_bytes() == payload
    assert first["rows"] == second["rows"] == 1
    assert second["methods"] == {"existing": 1}


def test_materialized_view_refuses_untracked_extra_file(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    payload = b"fixture-image"
    source = source_root / "commons" / "ragdoll" / "sample.jpg"
    source.parent.mkdir(parents=True)
    source.write_bytes(payload)
    row = {
        "image_id": "sample",
        "label": "ragdoll",
        "source_kind": "wikimedia_commons",
        "split": "train",
        "exact_sha256": hashlib.sha256(payload).hexdigest(),
    }
    output = tmp_path / "view"
    extra = output / "train" / CLASS_DIRS["ragdoll"] / "extra.jpg"
    extra.parent.mkdir(parents=True)
    extra.write_bytes(b"extra")
    with pytest.raises(ValueError, match="unexpected files"):
        materialize_dataset_view(rows=[row], source_root=source_root, output_root=output)
