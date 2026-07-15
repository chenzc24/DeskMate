"""Build a minimal, self-validating handoff for Phase 1 human review."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LABELS = {"ragdoll", "singapura", "persian", "sphynx", "pallas", "not_target"}
SOURCE_DIRS = {
    "wikimedia_commons": "commons",
    "inaturalist": "inaturalist",
    "oxford_iiit_pet": "oxford_iiit_pet",
    "gbif": "gbif",
}
REQUIRED_FIELDS = {
    "image_id",
    "label",
    "source_kind",
    "source_dataset",
    "source_group_id",
    "duplicate_cluster_id",
    "batch",
    "decision",
    "reviewer",
    "second_decision",
    "second_reviewer",
    "notes",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_queue(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        missing = sorted(REQUIRED_FIELDS - set(fields))
        if missing:
            raise ValueError(f"review queue missing fields: {missing}")
        rows = [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
        ]
    return fields, rows


def validate_row(row: dict[str, str], seen: set[str]) -> None:
    image_id = row["image_id"]
    label = row["label"]
    batch = row["batch"]
    if not image_id or Path(image_id).name != image_id:
        raise ValueError(f"unsafe or empty image_id: {image_id!r}")
    if image_id in seen:
        raise ValueError(f"duplicate image_id: {image_id}")
    seen.add(image_id)
    if label not in LABELS:
        raise ValueError(f"unsupported label for {image_id}: {label}")
    if row["source_kind"] not in SOURCE_DIRS:
        raise ValueError(f"unsupported source_kind for {image_id}: {row['source_kind']}")
    if not batch.startswith(f"{label}-") or Path(batch).name != batch:
        raise ValueError(f"unsafe or mismatched batch for {image_id}: {batch}")


def find_candidate(source_root: Path, row: dict[str, str]) -> Path:
    source_dir = SOURCE_DIRS[row["source_kind"]]
    search_root = source_root / source_dir / row["label"]
    matches = sorted(path for path in search_root.rglob(f"{row['image_id']}.*") if path.is_file())
    if not matches:
        raise FileNotFoundError(
            f"expected at least one image for {row['image_id']}, found 0"
        )
    if len(matches) > 1:
        hashes = {sha256(path) for path in matches}
        if len(hashes) != 1:
            raise ValueError(
                f"image_id maps to different file contents: {row['image_id']}"
            )
    return matches[0]


def build_handoff(
    *,
    source_root: Path,
    queue_path: Path,
    readme_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    if output_dir.exists():
        raise FileExistsError(f"output already exists: {output_dir}")
    fields, rows = read_queue(queue_path)
    seen: set[str] = set()
    for row in rows:
        validate_row(row, seen)

    output_dir.mkdir(parents=True)
    shutil.copy2(readme_path, output_dir / "README.md")
    with (output_dir / "review_queue.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    inventory_rows: list[dict[str, str | int]] = []
    label_counts: Counter[str] = Counter()
    total_image_bytes = 0
    for row in rows:
        source = find_candidate(source_root, row)
        relative = Path("images") / row["label"] / (
            row["image_id"] + source.suffix.casefold()
        )
        destination = output_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        size = destination.stat().st_size
        total_image_bytes += size
        label_counts[row["label"]] += 1
        inventory_rows.append(
            {
                "image_id": row["image_id"],
                "label": row["label"],
                "batch": row["batch"],
                "relative_path": relative.as_posix(),
                "bytes": size,
                "sha256": sha256(destination),
            }
        )

    inventory_path = output_dir / "inventory.csv"
    with inventory_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["image_id", "label", "batch", "relative_path", "bytes", "sha256"],
        )
        writer.writeheader()
        writer.writerows(inventory_rows)

    summary: dict[str, object] = {
        "schema_version": 1,
        "status": "PENDING_HUMAN_REVIEW",
        "image_count": len(rows),
        "image_bytes": total_image_bytes,
        "label_counts": dict(sorted(label_counts.items())),
        "queue_sha256": sha256(output_dir / "review_queue.csv"),
        "inventory_sha256": sha256(inventory_path),
        "contact_sheets_included": False,
        "excluded": [
            "acquisition caches and logs",
            "contact sheets",
            "model/training/evaluation artifacts",
            "source provenance manifest",
            "video fixtures",
        ],
    }
    (output_dir / "handoff_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-root",
        type=Path,
        default=ROOT / "data" / "downloads" / "phase1_candidates",
    )
    parser.add_argument(
        "--queue",
        type=Path,
        default=ROOT
        / "data"
        / "downloads"
        / "phase1_candidates"
        / "review_batches"
        / "review_queue.csv",
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=ROOT / "data" / "downloads" / "phase1_candidates" / "README.md",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "data" / "downloads" / "phase1_review_handoff_minimal",
    )
    args = parser.parse_args()
    summary = build_handoff(
        source_root=args.source_root,
        queue_path=args.queue,
        readme_path=args.readme,
        output_dir=args.output_dir,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
