"""Build bounded contact sheets and a local human-review queue."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from build_pilot_contact_sheets import build_sheet, find_image


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--pilot-root", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    root = args.pilot_root or args.manifest.parent
    output_dir = args.output_dir or root / "review_batches"

    existing_decisions: dict[str, dict[str, str]] = {}
    existing_queue = output_dir / "review_queue.csv"
    if existing_queue.exists():
        with existing_queue.open("r", encoding="utf-8-sig", newline="") as handle:
            existing_decisions = {
                row["image_id"]: row for row in csv.DictReader(handle)
            }

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    with args.manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["review_status"] == "quarantine":
                groups[row["label"]].append(row)

    queue_path = output_dir / "review_queue.csv"
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[dict[str, object]] = []
    missing: list[str] = []
    queue_rows: list[dict[str, str]] = []
    for label, rows in sorted(groups.items()):
        rows.sort(key=lambda row: row["image_id"])
        for offset in range(0, len(rows), args.batch_size):
            batch = rows[offset : offset + args.batch_size]
            batch_number = offset // args.batch_size + 1
            entries: list[tuple[Path, str]] = []
            for row in batch:
                try:
                    image_path = find_image(
                        root, row["source_kind"], row["label"], row["image_id"]
                    )
                except FileNotFoundError:
                    missing.append(row["image_id"])
                    continue
                entries.append(
                    (
                        image_path,
                        f"{row['image_id']} | {row['duplicate_cluster_id'] or '-'}",
                    )
                )
                prior = existing_decisions.get(row["image_id"], {})
                queue_rows.append(
                    {
                        "image_id": row["image_id"],
                        "label": label,
                        "source_kind": row["source_kind"],
                        "source_dataset": row["source_dataset"],
                        "source_group_id": row["source_group_id"],
                        "duplicate_cluster_id": row["duplicate_cluster_id"],
                        "batch": f"{label}-{batch_number:03d}",
                        "decision": prior.get("decision", ""),
                        "reviewer": prior.get("reviewer", ""),
                        "second_decision": prior.get("second_decision", ""),
                        "second_reviewer": prior.get("second_reviewer", ""),
                        "notes": prior.get("notes", ""),
                    }
                )
            if not entries:
                continue
            output = output_dir / label / f"{label}_{batch_number:03d}.png"
            build_sheet(
                entries,
                title=f"Phase 1 / {label} / batch {batch_number:03d} / quarantine",
                output=output,
                columns=4,
            )
            outputs.append(
                {
                    "label": label,
                    "batch": batch_number,
                    "count": len(entries),
                    "path": str(output),
                }
            )

    fieldnames = [
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
    ]
    with queue_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(queue_rows)
    report = {
        "queue": str(queue_path),
        "rows": len(queue_rows),
        "outputs": outputs,
        "missing": missing,
        "ok": not missing,
    }
    (output_dir / "review_batches.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
