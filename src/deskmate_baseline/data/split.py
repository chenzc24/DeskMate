"""Fail-closed, group-aware Baseline dataset freezing and materialization."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from ..domain.contracts import INTERNAL_LABELS, REPORTABLE_LABELS
from .dataset_prep import find_local_image
from ..domain.manifest import MANIFEST_FIELDS
from .review import audit_review_queue


SPLITS = ("train", "val_select", "val_cal")
SPLIT_RATIOS = {"train": 0.85, "val_select": 0.10, "val_cal": 0.05}
CLASS_DIRS = {label: f"{index}_{label}" for index, label in enumerate(INTERNAL_LABELS)}


class GateB1NotReady(RuntimeError):
    """Raised when pending or invalid review evidence forbids a split freeze."""

    def __init__(self, report: dict[str, Any]) -> None:
        super().__init__("Gate B1 is not ready; refusing to freeze a split")
        self.report = report


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class _UnionFind:
    def __init__(self, values: Iterable[str]) -> None:
        self.parent = {value: value for value in values}

    def find(self, value: str) -> str:
        parent = self.parent[value]
        if parent != value:
            self.parent[value] = self.find(parent)
        return self.parent[value]

    def union(self, left: str, right: str) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            low, high = sorted((left_root, right_root))
            self.parent[high] = low


def _target_counts(total: int, ratios: dict[str, float]) -> dict[str, int]:
    raw = {split: total * ratios[split] for split in SPLITS}
    counts = {split: int(raw[split]) for split in SPLITS}
    remaining = total - sum(counts.values())
    order = sorted(SPLITS, key=lambda split: (-(raw[split] - counts[split]), SPLITS.index(split)))
    for split in order[:remaining]:
        counts[split] += 1
    return counts


def _group_rows(rows: list[dict[str, str]]) -> list[list[dict[str, str]]]:
    union = _UnionFind(row["image_id"] for row in rows)
    token_owner: dict[tuple[str, str], str] = {}
    for row in rows:
        tokens = [
            ("source", row["source_group_id"]),
            ("duplicate", row["duplicate_cluster_id"]),
            ("exact", row["exact_sha256"].casefold()),
        ]
        for kind, value in tokens:
            if not value:
                continue
            key = (kind, value)
            owner = token_owner.setdefault(key, row["image_id"])
            union.union(owner, row["image_id"])
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[union.find(row["image_id"])].append(row)
    result = []
    for group in grouped.values():
        labels = {row["label"] for row in group}
        if len(labels) != 1:
            raise ValueError(f"linked group crosses labels: {sorted(labels)}")
        result.append(sorted(group, key=lambda row: row["image_id"]))
    return result


def _allocate_label(
    rows: list[dict[str, str]], *, seed: int, ratios: dict[str, float]
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    groups = _group_rows(rows)
    targets = _target_counts(len(rows), ratios)
    counts = Counter({split: 0 for split in SPLITS})

    def group_order(group: list[dict[str, str]]) -> str:
        ids = ",".join(row["image_id"] for row in group)
        return hashlib.sha256(f"{seed}:{ids}".encode()).hexdigest()

    groups.sort(key=lambda group: (-len(group), group_order(group)))
    allocated: list[dict[str, str]] = []
    for group in groups:
        size = len(group)

        def score(split: str) -> tuple[float, int]:
            projected = dict(counts)
            projected[split] += size
            squared_error = sum(
                ((projected[name] - targets[name]) ** 2) / max(1, targets[name])
                for name in SPLITS
            )
            return squared_error, SPLITS.index(split)

        selected = min(SPLITS, key=score)
        counts[selected] += size
        for source in group:
            row = dict(source)
            row["split"] = selected
            allocated.append(row)

    return allocated, {
        "rows": len(rows),
        "groups": len(groups),
        "largest_group": max((len(group) for group in groups), default=0),
        "target_counts": targets,
        "actual_counts": {split: counts[split] for split in SPLITS},
    }


def build_frozen_split(
    *,
    manifest_path: Path,
    queue_path: Path,
    second_reviewer_required_for: set[str],
    release_floor_total: int,
    release_floor_per_class: int,
    preferred_per_class: int,
    not_target_floor: int,
    seed: int,
    ratios: dict[str, float] | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Return accepted split rows, or fail with the complete Gate B1 audit."""
    review = audit_review_queue(
        manifest_path=manifest_path,
        queue_path=queue_path,
        second_reviewer_required_for=second_reviewer_required_for,
        release_floor_total=release_floor_total,
        release_floor_per_class=release_floor_per_class,
        preferred_per_class=preferred_per_class,
        not_target_floor=not_target_floor,
    )
    if not review["ready_to_freeze_split"]:
        raise GateB1NotReady(review)
    ratios = dict(ratios or SPLIT_RATIOS)
    if tuple(ratios) != SPLITS or abs(sum(ratios.values()) - 1.0) > 1e-9:
        raise ValueError("split ratios must define train/val_select/val_cal and sum to 1")

    manifest = {row["image_id"]: row for row in _read_csv(manifest_path)}
    queue = _read_csv(queue_path)
    accepted: list[dict[str, str]] = []
    for decision in queue:
        if decision["decision"].casefold() != "accepted":
            continue
        row = dict(manifest[decision["image_id"]])
        row["review_status"] = "accepted"
        row["reviewer"] = decision["reviewer"]
        accepted.append(row)

    by_label: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in accepted:
        by_label[row["label"]].append(row)
    frozen: list[dict[str, str]] = []
    allocation: dict[str, Any] = {}
    for label in INTERNAL_LABELS:
        label_rows, label_report = _allocate_label(
            by_label[label], seed=seed, ratios=ratios
        )
        frozen.extend(label_rows)
        allocation[label] = label_report
    frozen.sort(key=lambda row: (INTERNAL_LABELS.index(row["label"]), row["image_id"]))
    report = {
        "schema_version": 1,
        "ready": True,
        "seed": seed,
        "ratios": ratios,
        "class_order": list(INTERNAL_LABELS),
        "source_manifest_sha256": _sha256(manifest_path),
        "review_queue_sha256": _sha256(queue_path),
        "rows": len(frozen),
        "allocation": allocation,
        "review_audit": review,
    }
    return frozen, report


def write_split_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in MANIFEST_FIELDS} for row in rows)


def materialize_dataset_view(
    *, rows: list[dict[str, str]], source_root: Path, output_root: Path
) -> dict[str, Any]:
    """Create an idempotent hard-link/copy view for Ultralytics classification."""
    split_dirs = {"train": "train", "val_select": "val", "val_cal": "val_cal"}
    expected: dict[Path, str] = {}
    methods = Counter()
    for row in rows:
        if row["label"] not in CLASS_DIRS or row["split"] not in split_dirs:
            raise ValueError(f"invalid frozen row: {row['image_id']}")
        source = find_local_image(source_root, row)
        if _sha256(source) != row["exact_sha256"].casefold():
            raise ValueError(f"source hash mismatch: {row['image_id']}")
        target = (
            output_root
            / split_dirs[row["split"]]
            / CLASS_DIRS[row["label"]]
            / f"{row['image_id']}{source.suffix.casefold()}"
        )
        expected[target] = row["exact_sha256"].casefold()
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if _sha256(target) != expected[target]:
                raise ValueError(f"existing target hash mismatch: {target}")
            methods["existing"] += 1
            continue
        try:
            os.link(source, target)
            methods["hardlink"] += 1
        except OSError:
            shutil.copy2(source, target)
            methods["copy"] += 1

    existing = {
        path
        for split_dir in split_dirs.values()
        for path in (output_root / split_dir).glob("*/*")
        if path.is_file()
    }
    extras = sorted(str(path) for path in existing - set(expected))
    if extras:
        raise ValueError(f"dataset view contains {len(extras)} unexpected files")
    index = {
        "schema_version": 1,
        "rows": len(rows),
        "class_dirs": CLASS_DIRS,
        "methods": dict(methods),
        "files": [
            {"path": str(path.relative_to(output_root)), "sha256": expected[path]}
            for path in sorted(expected, key=str)
        ],
    }
    (output_root / "dataset_index.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return index
