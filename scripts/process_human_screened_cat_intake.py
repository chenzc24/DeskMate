"""Audit and materialize a human-screened five-class cat-image intake."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
import tomllib
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
REPORTABLE_LABELS = ("ragdoll", "singapura", "persian", "sphynx", "pallas")
MANIFEST_FIELDS = (
    "intake_id",
    "label",
    "source_relative_path",
    "original_filename",
    "bytes",
    "width",
    "height",
    "image_format",
    "exact_sha256",
    "dhash64",
    "technical_status",
    "screening_status",
    "provenance_status",
    "source_dataset",
    "source_record_id",
    "source_page_url",
    "original_url",
    "source_group_id",
    "exact_cluster_id",
    "near_cluster_id",
    "materialized_relative_path",
    "notes",
)
DUPLICATE_REVIEW_FIELDS = (
    "cluster_id",
    "kind",
    "cross_label",
    "labels",
    "member_count",
    "member_intake_ids",
    "member_source_paths",
)


@dataclass(slots=True)
class IntakeImage:
    intake_id: str
    label: str
    path: Path
    source_relative_path: str
    original_filename: str
    size_bytes: int = 0
    width: int = 0
    height: int = 0
    image_format: str = ""
    exact_sha256: str = ""
    dhash64: str = ""
    technical_status: str = "candidate"
    provenance_status: str = "missing"
    source_dataset: str = "merged_human_screened_unknown"
    source_record_id: str = ""
    source_page_url: str = ""
    original_url: str = ""
    source_group_id: str = ""
    exact_cluster_id: str = ""
    near_cluster_id: str = ""
    materialized_relative_path: str = ""
    notes: str = ""


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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dhash64(image: Image.Image) -> str:
    gray = ImageOps.exif_transpose(image).convert("L").resize((9, 8))
    pixel_data = (
        gray.get_flattened_data()
        if hasattr(gray, "get_flattened_data")
        else gray.getdata()
    )
    pixels = list(pixel_data)
    bits = 0
    for row in range(8):
        for column in range(8):
            left = pixels[row * 9 + column]
            right = pixels[row * 9 + column + 1]
            bits = (bits << 1) | int(left > right)
    return f"{bits:016x}"


def hamming_distance(left: str, right: str) -> int:
    return (int(left, 16) ^ int(right, 16)).bit_count()


def load_config(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        config = tomllib.load(handle)
    if int(config.get("schema_version", 0)) != 1:
        raise ValueError("unsupported intake config schema")
    prefixes = config["folder_prefixes"]
    if set(prefixes) != set(REPORTABLE_LABELS):
        raise ValueError("folder_prefixes must define exactly the five target labels")
    return config


def resolve_project_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def map_folders(input_root: Path, prefixes: dict[str, str]) -> dict[str, Path]:
    directories = sorted(path for path in input_root.iterdir() if path.is_dir())
    mapping: dict[str, Path] = {}
    used: set[Path] = set()
    for label in REPORTABLE_LABELS:
        prefix = prefixes[label].casefold()
        matches = [path for path in directories if path.name.casefold().startswith(prefix)]
        if len(matches) != 1:
            raise ValueError(
                f"expected one folder starting with {prefixes[label]!r} for {label}, "
                f"found {len(matches)}"
            )
        mapping[label] = matches[0]
        used.add(matches[0])
    unknown = [path.name for path in directories if path not in used]
    if unknown:
        raise ValueError(f"unmapped intake folders: {unknown}")
    return mapping


def read_partial_ragdoll_provenance(folder: Path) -> dict[int, dict[str, str]]:
    csv_paths = sorted(folder.glob("*.csv"))
    if not csv_paths:
        return {}
    if len(csv_paths) != 1:
        raise ValueError("expected at most one Ragdoll provenance CSV")
    records: dict[int, dict[str, str]] = {}
    with csv_paths[0].open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"sample_number", "flickr_photo_id", "download_url", "flickr_page"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Ragdoll provenance CSV is missing required fields")
        for row in reader:
            number = int(row["sample_number"])
            if number in records:
                raise ValueError(f"duplicate Ragdoll provenance sample: {number}")
            records[number] = {key: (value or "").strip() for key, value in row.items()}
    return records


def ragdoll_sample_number(path: Path) -> int | None:
    stem = path.stem
    suffix = stem.rsplit("_", 1)[-1]
    return int(suffix) if suffix.isdigit() else None


def scan_intake(
    input_root: Path,
    *,
    prefixes: dict[str, str],
    allowed_extensions: set[str],
    minimum_width: int,
    minimum_height: int,
) -> tuple[list[IntakeImage], list[dict[str, str]], dict[str, str]]:
    folders = map_folders(input_root, prefixes)
    ragdoll_provenance = read_partial_ragdoll_provenance(folders["ragdoll"])
    rows: list[IntakeImage] = []
    decode_errors: list[dict[str, str]] = []
    folder_names = {label: folder.name for label, folder in folders.items()}
    for label in REPORTABLE_LABELS:
        folder = folders[label]
        paths = sorted(
            path
            for path in folder.iterdir()
            if path.is_file() and path.suffix.casefold() in allowed_extensions
        )
        for index, path in enumerate(paths, start=1):
            row = IntakeImage(
                intake_id=f"{label}-{index:06d}",
                label=label,
                path=path,
                source_relative_path=path.relative_to(input_root).as_posix(),
                original_filename=path.name,
            )
            try:
                data = path.read_bytes()
                with Image.open(path) as image:
                    image.verify()
                with Image.open(path) as image:
                    oriented = ImageOps.exif_transpose(image)
                    row.width, row.height = oriented.size
                    row.image_format = (image.format or path.suffix.lstrip(".")).upper()
                    row.dhash64 = dhash64(image)
                row.size_bytes = len(data)
                row.exact_sha256 = sha256_bytes(data)
                if row.width < minimum_width or row.height < minimum_height:
                    row.technical_status = "rejected_below_minimum"
                    row.notes = (
                        f"dimensions {row.width}x{row.height} below "
                        f"{minimum_width}x{minimum_height}"
                    )
                if label == "ragdoll":
                    number = ragdoll_sample_number(path)
                    record = ragdoll_provenance.get(number or -1)
                    if record:
                        row.provenance_status = "partial_flickr_urls_no_license_or_author"
                        row.source_dataset = "flickr_colleague_csv"
                        row.source_record_id = record["flickr_photo_id"]
                        row.source_page_url = record["flickr_page"]
                        row.original_url = record["download_url"]
                        row.source_group_id = f"flickr-photo-{record['flickr_photo_id']}"
            except Exception as exc:
                row.technical_status = "rejected_decode_error"
                row.notes = str(exc)
                decode_errors.append(
                    {"source_relative_path": row.source_relative_path, "error": str(exc)}
                )
            rows.append(row)
    return rows, decode_errors, folder_names


def apply_exact_duplicate_policy(rows: list[IntakeImage]) -> list[dict[str, Any]]:
    groups: dict[str, list[IntakeImage]] = defaultdict(list)
    for row in rows:
        if row.exact_sha256:
            groups[row.exact_sha256].append(row)
    evidence: list[dict[str, Any]] = []
    for exact_hash, group in sorted(groups.items()):
        if len(group) < 2:
            continue
        ordered = sorted(group, key=lambda row: (row.label, row.source_relative_path))
        labels = sorted({row.label for row in ordered})
        cluster_id = f"exact-{exact_hash[:12]}"
        for row in ordered:
            row.exact_cluster_id = cluster_id
        if len(labels) > 1:
            for row in ordered:
                row.technical_status = "rejected_cross_label_exact"
                row.notes = "identical bytes appear under different labels"
            canonical = ""
        else:
            eligible = [row for row in ordered if row.technical_status == "candidate"]
            canonical = eligible[0].intake_id if eligible else ""
            for row in eligible[1:]:
                row.technical_status = "rejected_redundant_exact"
                row.notes = f"redundant exact copy of {canonical}"
        evidence.append(
            {
                "cluster_id": cluster_id,
                "labels": labels,
                "canonical": canonical,
                "members": [row.intake_id for row in ordered],
                "source_paths": [row.source_relative_path for row in ordered],
            }
        )
    return evidence


def assign_near_duplicate_clusters(
    rows: list[IntakeImage], threshold: int
) -> tuple[list[dict[str, Any]], int]:
    candidates = sorted(
        (row for row in rows if row.technical_status == "candidate"),
        key=lambda row: row.intake_id,
    )
    union = UnionFind(row.intake_id for row in candidates)
    pair_edges = 0
    for index, left in enumerate(candidates):
        for right in candidates[index + 1 :]:
            if hamming_distance(left.dhash64, right.dhash64) <= threshold:
                union.union(left.intake_id, right.intake_id)
                pair_edges += 1
    groups: dict[str, list[IntakeImage]] = defaultdict(list)
    for row in candidates:
        groups[union.find(row.intake_id)].append(row)
    evidence: list[dict[str, Any]] = []
    for group in sorted(
        (sorted(value, key=lambda row: row.intake_id) for value in groups.values() if len(value) > 1),
        key=lambda value: value[0].intake_id,
    ):
        digest_input = "|".join(row.intake_id for row in group).encode("utf-8")
        cluster_id = f"near-{hashlib.sha256(digest_input).hexdigest()[:12]}"
        for row in group:
            row.near_cluster_id = cluster_id
        labels = sorted({row.label for row in group})
        evidence.append(
            {
                "cluster_id": cluster_id,
                "labels": labels,
                "cross_label": len(labels) > 1,
                "members": [row.intake_id for row in group],
                "source_paths": [row.source_relative_path for row in group],
            }
        )
    return evidence, pair_edges


def manifest_row(row: IntakeImage, screening_status: str) -> dict[str, str | int]:
    return {
        "intake_id": row.intake_id,
        "label": row.label,
        "source_relative_path": row.source_relative_path,
        "original_filename": row.original_filename,
        "bytes": row.size_bytes,
        "width": row.width,
        "height": row.height,
        "image_format": row.image_format,
        "exact_sha256": row.exact_sha256,
        "dhash64": row.dhash64,
        "technical_status": row.technical_status,
        "screening_status": screening_status,
        "provenance_status": row.provenance_status,
        "source_dataset": row.source_dataset,
        "source_record_id": row.source_record_id,
        "source_page_url": row.source_page_url,
        "original_url": row.original_url,
        "source_group_id": row.source_group_id,
        "exact_cluster_id": row.exact_cluster_id,
        "near_cluster_id": row.near_cluster_id,
        "materialized_relative_path": row.materialized_relative_path,
        "notes": row.notes,
    }


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def process_intake(
    *,
    config_path: Path,
    input_root: Path,
    output_root: Path,
    materialize: bool = True,
) -> dict[str, Any]:
    config = load_config(config_path)
    if output_root.exists():
        raise FileExistsError(f"output already exists: {output_root}")
    technical = config["technical"]
    rows, decode_errors, folder_names = scan_intake(
        input_root,
        prefixes={key: str(value) for key, value in config["folder_prefixes"].items()},
        allowed_extensions={str(value).casefold() for value in technical["allowed_extensions"]},
        minimum_width=int(technical["minimum_width"]),
        minimum_height=int(technical["minimum_height"]),
    )
    exact_groups = apply_exact_duplicate_policy(rows)
    near_groups, near_pair_edges = assign_near_duplicate_clusters(
        rows, int(technical["near_duplicate_hamming_distance"])
    )

    output_root.mkdir(parents=True)
    if materialize:
        for row in rows:
            if row.technical_status != "candidate":
                continue
            relative = Path("clean_candidates") / row.label / (
                row.intake_id + row.path.suffix.casefold()
            )
            destination = output_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(row.path, destination)
            if sha256_file(destination) != row.exact_sha256:
                raise RuntimeError(f"materialized copy hash mismatch: {relative}")
            row.materialized_relative_path = relative.as_posix()

    screening_status = str(config["screening"]["status"])
    manifest_path = output_root / "intake_manifest.csv"
    manifest_rows = [manifest_row(row, screening_status) for row in rows]
    write_csv(manifest_path, MANIFEST_FIELDS, manifest_rows)

    duplicate_rows: list[dict[str, Any]] = []
    for group in exact_groups:
        duplicate_rows.append(
            {
                "cluster_id": group["cluster_id"],
                "kind": "exact",
                "cross_label": len(group["labels"]) > 1,
                "labels": "|".join(group["labels"]),
                "member_count": len(group["members"]),
                "member_intake_ids": "|".join(group["members"]),
                "member_source_paths": "|".join(group["source_paths"]),
            }
        )
    for group in near_groups:
        duplicate_rows.append(
            {
                "cluster_id": group["cluster_id"],
                "kind": "near_dhash",
                "cross_label": group["cross_label"],
                "labels": "|".join(group["labels"]),
                "member_count": len(group["members"]),
                "member_intake_ids": "|".join(group["members"]),
                "member_source_paths": "|".join(group["source_paths"]),
            }
        )
    duplicate_path = output_root / "duplicate_review.csv"
    write_csv(duplicate_path, DUPLICATE_REVIEW_FIELDS, duplicate_rows)

    raw_counts = Counter(row.label for row in rows)
    status_counts = Counter(row.technical_status for row in rows)
    candidate_counts = Counter(
        row.label for row in rows if row.technical_status == "candidate"
    )
    provenance_counts = Counter(row.provenance_status for row in rows)
    below_counts = Counter(
        row.label for row in rows if row.technical_status == "rejected_below_minimum"
    )
    exact_redundant_counts = Counter(
        row.label for row in rows if row.technical_status == "rejected_redundant_exact"
    )
    cross_label_exact = [group for group in exact_groups if len(group["labels"]) > 1]
    cross_label_near = [group for group in near_groups if group["cross_label"]]
    targets = config["targets"]
    candidate_total = sum(candidate_counts.values())
    release_floor_ready = (
        candidate_total >= int(targets["release_floor_total"])
        and all(
            candidate_counts[label] >= int(targets["release_floor_per_class"])
            for label in REPORTABLE_LABELS
        )
    )
    preferred_ready = all(
        candidate_counts[label] >= int(targets["preferred_per_class"])
        for label in REPORTABLE_LABELS
    )
    snapshot_lines = [
        f"{row.source_relative_path}\0{row.exact_sha256}" for row in rows
    ]
    input_snapshot_sha256 = hashlib.sha256(
        "\n".join(snapshot_lines).encode("utf-8")
    ).hexdigest()
    blockers = [
        "not_target_not_present_in_this_intake",
        "provenance_and_license_incomplete",
        "source_session_groups_incomplete",
        "near_duplicate_clusters_require_human_confirmation",
    ]
    if cross_label_near:
        blockers.append("cross_label_near_hash_collisions_require_human_review")
    if cross_label_exact:
        blockers.append("cross_label_exact_duplicates")

    audit: dict[str, Any] = {
        "schema_version": 1,
        "status": "PROCESSED_NOT_READY_FOR_SPLIT_OR_TRAINING",
        "screening_status": screening_status,
        "folder_names": folder_names,
        "raw_image_count": len(rows),
        "raw_counts": dict(sorted(raw_counts.items())),
        "decoded_count": len(rows) - len(decode_errors),
        "decode_errors": decode_errors,
        "technical_status_counts": dict(sorted(status_counts.items())),
        "below_minimum_counts": dict(sorted(below_counts.items())),
        "exact_duplicate_group_count": len(exact_groups),
        "exact_redundant_counts": dict(sorted(exact_redundant_counts.items())),
        "cross_label_exact_group_count": len(cross_label_exact),
        "near_duplicate_threshold": int(technical["near_duplicate_hamming_distance"]),
        "near_duplicate_pair_edges": near_pair_edges,
        "near_duplicate_cluster_count": len(near_groups),
        "near_duplicate_images": sum(len(group["members"]) for group in near_groups),
        "cross_label_near_cluster_count": len(cross_label_near),
        "candidate_counts": {
            label: candidate_counts[label] for label in REPORTABLE_LABELS
        },
        "candidate_total": candidate_total,
        "provenance_counts": dict(sorted(provenance_counts.items())),
        "release_floor_target_only_ready": release_floor_ready,
        "preferred_target_only_ready": preferred_ready,
        "not_target_count": 0,
        "gate_b1_ready": False,
        "ready_for_training": False,
        "blockers": blockers,
        "config_sha256": sha256_file(config_path),
        "input_snapshot_sha256": input_snapshot_sha256,
        "manifest_sha256": sha256_file(manifest_path),
        "duplicate_review_sha256": sha256_file(duplicate_path),
        "originals_modified": False,
        "materialization": str(technical["materialization"]) if materialize else "none",
    }
    audit_path = output_root / "audit.json"
    audit_path.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_root / "README.md").write_text(
        "# Generated Human-Screened Cat Intake\n\n"
        "This ignored directory is generated by "
        "`scripts/process_human_screened_cat_intake.py`. The source directory "
        "`data/downloads/cat` remains read-only. `clean_candidates` excludes "
        "technical failures and redundant exact copies, but it is not a frozen "
        "training split. See `audit.json` for blockers.\n",
        encoding="utf-8",
    )
    return audit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "baseline_human_screened_intake.toml",
    )
    parser.add_argument("--input-root", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--no-materialize", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config)
    input_root = args.input_root or resolve_project_path(config["paths"]["input_root"])
    output_root = args.output_root or resolve_project_path(config["paths"]["output_root"])
    audit = process_intake(
        config_path=args.config,
        input_root=input_root,
        output_root=output_root,
        materialize=not args.no_materialize,
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not audit["decode_errors"] and not audit["cross_label_exact_group_count"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
