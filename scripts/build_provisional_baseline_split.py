"""Build a development-only six-class split while official Gate B1 stays closed."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
import tomllib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from deskmate_baseline.contracts import INTERNAL_LABELS, REPORTABLE_LABELS  # noqa: E402
from deskmate_baseline.dataset_prep import find_local_image  # noqa: E402


SPLITS = ("train", "val_select", "val_cal")
CLASS_DIRS = {label: f"{index}_{label}" for index, label in enumerate(INTERNAL_LABELS)}
MANIFEST_FIELDS = (
    "sample_id",
    "label",
    "split",
    "source_kind",
    "source_image_id",
    "source_relative_path",
    "exact_sha256",
    "source_group_id",
    "duplicate_group_id",
    "review_state",
    "provenance_state",
    "risk_state",
    "materialized_relative_path",
)


class UnionFind:
    def __init__(self, values: Iterable[str]) -> None:
        self.parent = {value: value for value in values}

    def find(self, value: str) -> str:
        parent = self.parent[value]
        if parent != value:
            self.parent[value] = self.find(parent)
        return self.parent[value]

    def union(self, left: str, right: str) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root == right_root:
            return
        low, high = sorted((left_root, right_root))
        self.parent[high] = low


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in MANIFEST_FIELDS} for row in rows)


def load_config(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        config = tomllib.load(handle)
    if int(config.get("schema_version", 0)) != 1:
        raise ValueError("unsupported provisional dataset config schema")
    ratios = config["split"]
    if abs(sum(float(ratios[name]) for name in SPLITS) - 1.0) > 1e-9:
        raise ValueError("provisional split ratios must sum to one")
    return config


def project_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def target_rows(manifest_path: Path, target_root: Path, status: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in read_csv(manifest_path):
        if row["technical_status"] != status:
            continue
        label = row["label"]
        if label not in REPORTABLE_LABELS:
            raise ValueError(f"unexpected target label: {label}")
        path = target_root / row["materialized_relative_path"]
        if not path.is_file():
            raise FileNotFoundError(path)
        if sha256_file(path) != row["exact_sha256"].casefold():
            raise ValueError(f"target source hash mismatch: {row['intake_id']}")
        result.append(
            {
                "sample_id": f"target-{row['intake_id']}",
                "label": label,
                "source_kind": "human_screened_intake",
                "source_image_id": row["intake_id"],
                "source_relative_path": row["materialized_relative_path"],
                "source_path": path,
                "exact_sha256": row["exact_sha256"].casefold(),
                "source_group_id": row["source_group_id"],
                "duplicate_group_id": row["near_cluster_id"],
                "review_state": row["screening_status"],
                "provenance_state": row["provenance_status"],
                "risk_state": "provenance_deferred;source_session_incomplete",
                "split": "",
                "materialized_relative_path": "",
            }
        )
    return result


def negative_rows(
    manifest_path: Path,
    negative_root: Path,
    *,
    label: str,
    status: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in read_csv(manifest_path):
        if row["label"] != label or row["review_status"] != status:
            continue
        path = find_local_image(negative_root, row)
        if sha256_file(path) != row["exact_sha256"].casefold():
            raise ValueError(f"negative source hash mismatch: {row['image_id']}")
        result.append(
            {
                "sample_id": f"negative-{row['image_id']}",
                "label": "not_target",
                "source_kind": row["source_kind"],
                "source_image_id": row["image_id"],
                "source_relative_path": path.relative_to(negative_root).as_posix(),
                "source_path": path,
                "exact_sha256": row["exact_sha256"].casefold(),
                "source_group_id": row["source_group_id"],
                "duplicate_group_id": row["duplicate_cluster_id"],
                "review_state": "phase1_review_pending_allowed_provisionally",
                "provenance_state": "phase1_manifest_recorded",
                "risk_state": "negative_human_review_pending",
                "split": "",
                "materialized_relative_path": "",
            }
        )
    return result


def deduplicate_exact(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["exact_sha256"]].append(row)
    retained: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for exact_hash, group in sorted(groups.items()):
        ordered = sorted(group, key=lambda row: row["sample_id"])
        labels = sorted({row["label"] for row in ordered})
        if len(labels) > 1:
            raise ValueError(
                f"cross-label exact content {exact_hash[:12]}: {labels}"
            )
        retained.append(ordered[0])
        for row in ordered[1:]:
            dropped.append(
                {
                    "sample_id": row["sample_id"],
                    "canonical": ordered[0]["sample_id"],
                    "label": row["label"],
                    "exact_sha256": exact_hash,
                }
            )
    return sorted(retained, key=lambda row: row["sample_id"]), dropped


def target_counts(total: int, ratios: dict[str, float]) -> dict[str, int]:
    raw = {name: total * ratios[name] for name in SPLITS}
    counts = {name: int(raw[name]) for name in SPLITS}
    remaining = total - sum(counts.values())
    order = sorted(SPLITS, key=lambda name: (-(raw[name] - counts[name]), SPLITS.index(name)))
    for name in order[:remaining]:
        counts[name] += 1
    return counts


def grouped_components(rows: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    union = UnionFind(row["sample_id"] for row in rows)
    owners: dict[tuple[str, str], str] = {}
    for row in rows:
        for kind, value in (
            ("source", row["source_group_id"]),
            ("duplicate", row["duplicate_group_id"]),
            ("exact", row["exact_sha256"]),
        ):
            if not value:
                continue
            owner = owners.setdefault((kind, value), row["sample_id"])
            union.union(owner, row["sample_id"])
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[union.find(row["sample_id"])].append(row)
    return [sorted(group, key=lambda row: row["sample_id"]) for group in groups.values()]


def allocate_label(
    rows: list[dict[str, Any]], *, seed: int, ratios: dict[str, float]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    groups = grouped_components(rows)
    targets = target_counts(len(rows), ratios)
    counts = Counter({name: 0 for name in SPLITS})

    def order_key(group: list[dict[str, Any]]) -> str:
        ids = ",".join(row["sample_id"] for row in group)
        return hashlib.sha256(f"{seed}:{ids}".encode()).hexdigest()

    groups.sort(key=lambda group: (-len(group), order_key(group)))
    allocated: list[dict[str, Any]] = []
    for group in groups:
        size = len(group)

        def score(split: str) -> tuple[float, int]:
            projected = dict(counts)
            projected[split] += size
            error = sum(
                ((projected[name] - targets[name]) ** 2) / max(1, targets[name])
                for name in SPLITS
            )
            return error, SPLITS.index(split)

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
        "actual_counts": {name: counts[name] for name in SPLITS},
    }


def allocate_all(
    rows: list[dict[str, Any]], *, seed: int, ratios: dict[str, float]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_label[row["label"]].append(row)
    frozen: list[dict[str, Any]] = []
    allocation: dict[str, Any] = {}
    for label in INTERNAL_LABELS:
        allocated, report = allocate_label(by_label[label], seed=seed, ratios=ratios)
        frozen.extend(allocated)
        allocation[label] = report
    frozen.sort(key=lambda row: (INTERNAL_LABELS.index(row["label"]), row["sample_id"]))
    return frozen, allocation


def materialize(rows: list[dict[str, Any]], output_root: Path) -> dict[str, Any]:
    split_dirs = {"train": "train", "val_select": "val", "val_cal": "val_cal"}
    counts: Counter[str] = Counter()
    for row in rows:
        source = Path(row["source_path"])
        relative = (
            Path("yolo_classify")
            / split_dirs[row["split"]]
            / CLASS_DIRS[row["label"]]
            / f"{row['sample_id']}{source.suffix.casefold()}"
        )
        destination = output_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        if sha256_file(destination) != row["exact_sha256"]:
            raise RuntimeError(f"materialized hash mismatch: {relative}")
        row["materialized_relative_path"] = relative.as_posix()
        counts[f"{row['split']}:{row['label']}"] += 1
    return {"method": "copy", "files": len(rows), "counts": dict(sorted(counts.items()))}


def build_dataset(
    *, config_path: Path, output_root: Path | None = None, materialize_files: bool = True
) -> dict[str, Any]:
    config = load_config(config_path)
    paths = config["paths"]
    selected_output = output_root or project_path(paths["output_root"])
    if selected_output.exists():
        raise FileExistsError(f"output already exists: {selected_output}")
    target_manifest = project_path(paths["target_manifest"])
    target_root = project_path(paths["target_root"])
    negative_manifest = project_path(paths["negative_manifest"])
    negative_root = project_path(paths["negative_root"])
    selection = config["selection"]
    rows = target_rows(target_manifest, target_root, str(selection["target_status"]))
    rows.extend(
        negative_rows(
            negative_manifest,
            negative_root,
            label=str(selection["negative_label"]),
            status=str(selection["negative_status"]),
        )
    )
    rows, exact_dropped = deduplicate_exact(rows)
    ratios = {name: float(config["split"][name]) for name in SPLITS}
    frozen, allocation = allocate_all(
        rows, seed=int(config["split"]["seed"]), ratios=ratios
    )
    selected_output.mkdir(parents=True)
    materialization = (
        materialize(frozen, selected_output)
        if materialize_files
        else {"method": "none", "files": 0, "counts": {}}
    )
    manifest_path = selected_output / "provisional_split_manifest.csv"
    write_csv(manifest_path, frozen)
    class_counts = Counter(row["label"] for row in frozen)
    floors = config["release_floor"]
    target_total = sum(class_counts[label] for label in REPORTABLE_LABELS)
    floor_ready = (
        target_total >= int(floors["target_total"])
        and all(class_counts[label] >= int(floors["target_per_class"]) for label in REPORTABLE_LABELS)
        and class_counts["not_target"] >= int(floors["not_target"])
    )
    report: dict[str, Any] = {
        "schema_version": 1,
        "status": "PROVISIONAL_DEVELOPMENT_SPLIT_READY" if floor_ready else "PROVISIONAL_SPLIT_BELOW_FLOOR",
        "official_gate_b1_ready": False,
        "provisional_training_data_ready": floor_ready,
        "class_order": list(INTERNAL_LABELS),
        "ratios": ratios,
        "seed": int(config["split"]["seed"]),
        "rows": len(frozen),
        "class_counts": {label: class_counts[label] for label in INTERNAL_LABELS},
        "allocation": allocation,
        "exact_duplicates_dropped": exact_dropped,
        "materialization": materialization,
        "deferred_risks": [
            "target_author_and_license_completion",
            "target_source_session_reconstruction",
            "not_target_human_review_completion",
            "cross_label_dhash_only_collision_adjudication",
        ],
        "risk_scope": "development_only_not_final_release",
        "input_checksums": {
            "config_sha256": sha256_file(config_path),
            "target_manifest_sha256": sha256_file(target_manifest),
            "negative_manifest_sha256": sha256_file(negative_manifest),
        },
        "manifest_sha256": sha256_file(manifest_path),
    }
    (selected_output / "provisional_split_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "baseline_provisional_dataset.toml",
    )
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--no-materialize", action="store_true")
    args = parser.parse_args()
    report = build_dataset(
        config_path=args.config,
        output_root=args.output_root,
        materialize_files=not args.no_materialize,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["provisional_training_data_ready"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
