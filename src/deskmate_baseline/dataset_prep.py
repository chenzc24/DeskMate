"""Deterministic technical preparation for human-reviewed Baseline candidates."""

from __future__ import annotations

import csv
import hashlib
import io
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit

from PIL import Image, ImageOps

from .contracts import INTERNAL_LABELS, REPORTABLE_LABELS
from .manifest import MANIFEST_FIELDS


SOURCE_DIRS = {
    "wikimedia_commons": "commons",
    "inaturalist": "inaturalist",
    "oxford_iiit_pet": "oxford_iiit_pet",
    "gbif": "gbif",
}
SOURCE_PRIORITY = {
    "oxford_iiit_pet": 0,
    "inaturalist": 1,
    "wikimedia_commons": 2,
    "gbif": 3,
}


def dhash64(data: bytes) -> str:
    """Return a stable 64-bit difference hash for near-duplicate triage."""
    with Image.open(io.BytesIO(data)) as image:
        grayscale = ImageOps.exif_transpose(image).convert("L").resize((9, 8))
        pixel_data = (
            grayscale.get_flattened_data()
            if hasattr(grayscale, "get_flattened_data")
            else grayscale.getdata()
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


def find_local_image(root: Path, row: dict[str, str]) -> Path:
    source_dir = SOURCE_DIRS[row["source_kind"]]
    matches = sorted(
        path
        for path in (root / source_dir / row["label"]).rglob(f"{row['image_id']}.*")
        if path.is_file() and path.suffix.casefold() in {".jpg", ".jpeg", ".png"}
    )
    if not matches:
        raise FileNotFoundError(row["image_id"])
    return matches[0]


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


def _stable_download_time(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).astimezone().isoformat(
        timespec="seconds"
    )


def normalize_original_url(value: str) -> str:
    parts = urlsplit(value.strip())
    scheme = "https" if parts.scheme in {"http", "https"} else parts.scheme
    return urlunsplit(
        (scheme, parts.netloc.casefold(), parts.path, "", parts.fragment)
    )


def prepare_candidate_rows(
    rows: list[dict[str, str]],
    *,
    artifact_root: Path,
    minimum_width: int,
    minimum_height: int,
    near_duplicate_hamming_distance: int,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Validate, collapse, hash, and cluster candidates without accepting them."""
    id_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for source_row in rows:
        row = {field: str(source_row.get(field, "")) for field in MANIFEST_FIELDS}
        row["review_status"] = "quarantine"
        row["reviewer"] = ""
        row["duplicate_cluster_id"] = ""
        row["split"] = "staging"
        id_groups[row["image_id"]].append(row)

    prepared: list[dict[str, str]] = []
    collapsed_id_aliases: list[dict[str, Any]] = []
    id_label_conflicts: list[dict[str, Any]] = []
    for image_id, group in sorted(id_groups.items()):
        ordered = sorted(group, key=lambda row: (row["label"], row["source_dataset"]))
        labels = sorted({row["label"] for row in ordered})
        chosen = ordered[0]
        if len(labels) > 1:
            chosen["review_status"] = "rejected"
            chosen["duplicate_cluster_id"] = f"id-conflict-{image_id}"
            id_label_conflicts.append({"image_id": image_id, "labels": labels})
        elif len(ordered) > 1:
            collapsed_id_aliases.append(
                {
                    "image_id": image_id,
                    "label": labels[0],
                    "source_datasets": [row["source_dataset"] for row in ordered],
                }
            )
        prepared.append(chosen)

    technical_rejections: list[dict[str, str]] = []
    local_paths: dict[str, str] = {}
    for row in prepared:
        try:
            path = find_local_image(artifact_root, row)
            data = path.read_bytes()
            actual_hash = hashlib.sha256(data).hexdigest()
            if actual_hash != row["exact_sha256"]:
                raise ValueError("downloaded bytes do not match manifest SHA-256")
            width, height = int(row["width"]), int(row["height"])
            row["perceptual_hash"] = dhash64(data)
            row["downloaded_at"] = _stable_download_time(path)
            local_paths[row["image_id"]] = str(path)
            if width < minimum_width or height < minimum_height:
                row["review_status"] = "rejected"
                technical_rejections.append(
                    {
                        "image_id": row["image_id"],
                        "reason": f"dimensions {width}x{height} below minimum",
                    }
                )
        except Exception as exc:
            row["review_status"] = "rejected"
            technical_rejections.append(
                {"image_id": row["image_id"], "reason": str(exc)}
            )

    exact_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in prepared:
        if row["review_status"] == "quarantine":
            exact_groups[row["exact_sha256"]].append(row)
    exact_duplicate_clusters: list[dict[str, Any]] = []
    exact_label_conflicts: list[dict[str, Any]] = []
    for exact_hash, group in sorted(exact_groups.items()):
        if len(group) < 2:
            continue
        ordered = sorted(group, key=lambda row: row["image_id"])
        labels = sorted({row["label"] for row in ordered})
        cluster_id = f"exact-{exact_hash[:12]}"
        for row in ordered:
            row["duplicate_cluster_id"] = cluster_id
        if len(labels) > 1:
            for row in ordered:
                row["review_status"] = "rejected"
            exact_label_conflicts.append(
                {
                    "cluster_id": cluster_id,
                    "labels": labels,
                    "image_ids": [row["image_id"] for row in ordered],
                }
            )
        else:
            for row in ordered[1:]:
                row["review_status"] = "rejected"
            exact_duplicate_clusters.append(
                {
                    "cluster_id": cluster_id,
                    "label": labels[0],
                    "canonical": ordered[0]["image_id"],
                    "duplicates": [row["image_id"] for row in ordered[1:]],
                }
            )

    url_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in prepared:
        if row["review_status"] == "quarantine" and row["original_url"]:
            url_groups[normalize_original_url(row["original_url"])].append(row)
    url_duplicate_clusters: list[dict[str, Any]] = []
    url_label_conflicts: list[dict[str, Any]] = []
    for normalized_url, group in sorted(url_groups.items()):
        if len(group) < 2:
            continue
        ordered = sorted(
            group,
            key=lambda row: (
                SOURCE_PRIORITY.get(row["source_kind"], 99),
                row["image_id"],
            ),
        )
        labels = sorted({row["label"] for row in ordered})
        cluster_id = f"url-{hashlib.sha256(normalized_url.encode()).hexdigest()[:12]}"
        for row in ordered:
            if not row["duplicate_cluster_id"]:
                row["duplicate_cluster_id"] = cluster_id
        if len(labels) > 1:
            for row in ordered:
                row["review_status"] = "rejected"
            url_label_conflicts.append(
                {
                    "cluster_id": cluster_id,
                    "labels": labels,
                    "image_ids": [row["image_id"] for row in ordered],
                }
            )
        else:
            for row in ordered[1:]:
                row["review_status"] = "rejected"
            url_duplicate_clusters.append(
                {
                    "cluster_id": cluster_id,
                    "label": labels[0],
                    "canonical": ordered[0]["image_id"],
                    "duplicates": [row["image_id"] for row in ordered[1:]],
                }
            )

    near_duplicate_clusters: list[dict[str, Any]] = []
    for label in INTERNAL_LABELS:
        candidates = sorted(
            (row for row in prepared if row["label"] == label and row["review_status"] == "quarantine"),
            key=lambda row: row["image_id"],
        )
        union = UnionFind(row["image_id"] for row in candidates)
        for index, left in enumerate(candidates):
            for right in candidates[index + 1 :]:
                if hamming_distance(left["perceptual_hash"], right["perceptual_hash"]) <= near_duplicate_hamming_distance:
                    union.union(left["image_id"], right["image_id"])
        clusters: dict[str, list[str]] = defaultdict(list)
        for row in candidates:
            clusters[union.find(row["image_id"])].append(row["image_id"])
        by_id = {row["image_id"]: row for row in candidates}
        for image_ids in sorted(clusters.values()):
            if len(image_ids) < 2:
                continue
            image_ids.sort()
            cluster_id = f"near-{image_ids[0]}"
            for image_id in image_ids:
                if not by_id[image_id]["duplicate_cluster_id"]:
                    by_id[image_id]["duplicate_cluster_id"] = cluster_id
            near_duplicate_clusters.append(
                {"cluster_id": cluster_id, "label": label, "image_ids": image_ids}
            )

    prepared.sort(key=lambda row: (INTERNAL_LABELS.index(row["label"]), row["image_id"]))
    candidate_counts = Counter(
        row["label"] for row in prepared if row["review_status"] == "quarantine"
    )
    rejected_counts = Counter(
        row["label"] for row in prepared if row["review_status"] == "rejected"
    )
    report = {
        "schema_version": 1,
        "raw_rows": len(rows),
        "manifest_rows": len(prepared),
        "candidate_unique": {label: candidate_counts[label] for label in INTERNAL_LABELS},
        "rejected": {label: rejected_counts[label] for label in INTERNAL_LABELS},
        "accepted_unique": {label: 0 for label in INTERNAL_LABELS},
        "collapsed_id_aliases": collapsed_id_aliases,
        "id_label_conflicts": id_label_conflicts,
        "technical_rejections": technical_rejections,
        "exact_duplicate_clusters": exact_duplicate_clusters,
        "exact_label_conflicts": exact_label_conflicts,
        "url_duplicate_clusters": url_duplicate_clusters,
        "url_label_conflicts": url_label_conflicts,
        "near_duplicate_clusters": near_duplicate_clusters,
        "local_paths": local_paths,
        "automatic_acceptance": False,
    }
    return prepared, report


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def coverage_decision(
    preparation: dict[str, Any],
    *,
    release_floor_total: int,
    release_floor_per_class: int,
    preferred_per_class: int,
    not_target_floor: int,
) -> dict[str, Any]:
    counts = preparation["candidate_unique"]
    target_total = sum(counts[label] for label in REPORTABLE_LABELS)
    return {
        "candidate_target_total": target_total,
        "candidate_release_floor_ready": target_total >= release_floor_total
        and all(counts[label] >= release_floor_per_class for label in REPORTABLE_LABELS),
        "candidate_not_target_floor_ready": counts["not_target"] >= not_target_floor,
        "candidate_gap_to_preferred": {
            label: max(0, preferred_per_class - counts[label])
            for label in REPORTABLE_LABELS
        },
        "accepted_release_floor_ready": False,
        "selenium_authorized": False,
        "selenium_reason": (
            "Human accepted/post-dedup counts do not exist yet; candidate coverage alone "
            "cannot authorize gap-fill scraping."
        ),
    }
