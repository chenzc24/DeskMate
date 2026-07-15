from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import tomllib
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from deskmate_baseline.data.source_pilot import run_commons_pair  # noqa: E402


MANIFEST_FIELDS = (
    "review_filename",
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
    "width",
    "height",
    "review_status",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def local_source(source_roots: tuple[Path, ...], row: dict[str, str]) -> Path:
    image_id = row["image_id"]
    for root in source_roots:
        matches = list(root.rglob(f"{image_id}.*"))
        if matches:
            return matches[0]
    raise FileNotFoundError(f"no local source for {image_id}")


def materialize(
    *,
    label: str,
    rows: list[dict[str, str]],
    source_roots: tuple[Path, ...],
    output: Path,
    frozen_hashes: set[str],
    limit: int,
) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    selected: list[dict[str, str]] = []
    seen: set[str] = set()
    rejected = Counter()
    for row in sorted(rows, key=lambda item: (item["source_kind"], item["image_id"])):
        digest = row["exact_sha256"].casefold()
        if digest in frozen_hashes:
            rejected["already_in_frozen_split"] += 1
            continue
        if digest in seen:
            rejected["duplicate_in_new_pool"] += 1
            continue
        if int(row["width"]) < 160 or int(row["height"]) < 160:
            rejected["too_small"] += 1
            continue
        if not row["source_page_url"] or not row["license_name"] or not row["license_url"]:
            rejected["missing_provenance_or_license"] += 1
            continue
        source = local_source(source_roots, row)
        filename = f"{row['source_kind']}_{row['image_id']}{source.suffix.lower()}"
        shutil.copy2(source, output / filename)
        selected.append({key: row.get(key, "") for key in MANIFEST_FIELDS} | {"review_filename": filename, "review_status": "pending"})
        seen.add(digest)
        if len(selected) >= limit:
            break
    manifest = output / "manifest.csv"
    with manifest.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(selected)
    return {
        "label": label,
        "selected": len(selected),
        "source_counts": dict(Counter(row["source_kind"] for row in selected)),
        "rejected": dict(rejected),
        "folder": str(output),
        "manifest": str(manifest),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/downloads/baseline_additional_review_20260715"))
    parser.add_argument("--limit-per-class", type=int, default=220)
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    staging = output / "_source_downloads"
    config_path = ROOT / "configs" / "baseline_phase1_data.toml"
    with config_path.open("rb") as handle:
        config = tomllib.load(handle)
    frozen_rows = read_csv(ROOT / "data/downloads/baseline_provisional_split/provisional_split_manifest.csv")
    frozen_hashes = {row["exact_sha256"].casefold() for row in frozen_rows}
    phase1_root = ROOT / "data/downloads/phase1_candidates"
    phase1_rows = read_csv(phase1_root / "source_manifest.csv")
    commons = config["commons"]
    network = config["network"]
    singapura_rows, singapura_source = run_commons_pair(
        api_url=commons["api_url"],
        category="Singapura",
        label="singapura",
        limit=400,
        max_depth=network["commons_max_depth"],
        output_dir=staging,
        user_agent=config["user_agent"],
        timeout=network["request_timeout_seconds"],
        group_name="gapfill_20260715",
    )
    prior_singapura = [row for row in phase1_rows if row["label"] == "singapura"]
    prior_pallas = [row for row in phase1_rows if row["label"] == "pallas"]
    source_roots = (staging, phase1_root)
    reports = [
        materialize(label="singapura", rows=prior_singapura + singapura_rows, source_roots=source_roots, output=output / "singapura", frozen_hashes=frozen_hashes, limit=args.limit_per_class),
        materialize(label="pallas", rows=prior_pallas, source_roots=source_roots, output=output / "pallas", frozen_hashes=frozen_hashes, limit=args.limit_per_class),
    ]
    report = {
        "schema_version": 1,
        "status": "PENDING_HUMAN_REVIEW",
        "frozen_hash_count": len(frozen_hashes),
        "classes": reports,
        "source_reports": [
            singapura_source,
            {"source": "existing_phase1_candidates", "label": "singapura", "rows": len(prior_singapura)},
            {"source": "existing_phase1_candidates", "label": "pallas", "rows": len(prior_pallas)},
        ],
    }
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
