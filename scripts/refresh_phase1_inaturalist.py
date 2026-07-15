"""Refresh the Pallas source without re-running every Phase 1 acquisition."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from deskmate_baseline.dataset_prep import (  # noqa: E402
    coverage_decision,
    prepare_candidate_rows,
    write_rows,
)
from deskmate_baseline.manifest import audit_manifest  # noqa: E402
from deskmate_baseline.source_pilot import run_inaturalist_pallas  # noqa: E402


def main() -> int:
    config_path = ROOT / "configs" / "baseline_phase1_data.toml"
    with config_path.open("rb") as handle:
        config = tomllib.load(handle)
    output_dir = ROOT / config["paths"]["output_dir"]
    manifest_path = output_dir / "source_manifest.csv"
    report_path = output_dir / "candidate_report.full.json"
    prior_report = json.loads(report_path.read_text(encoding="utf-8"))
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        base_rows = [
            row
            for row in csv.DictReader(handle)
            if row["source_kind"] != "inaturalist"
        ]

    inat = config["inaturalist"]
    source_rows, source_report = run_inaturalist_pallas(
        api_url=inat["api_url"],
        taxon_id=inat["taxon_id"],
        label=inat["label"],
        allowed_licenses=set(inat["allowed_photo_licenses"]),
        limit=inat["limit"],
        output_dir=output_dir,
        user_agent=config["user_agent"],
        timeout=config["network"]["request_timeout_seconds"],
        max_pages=inat["max_api_pages"],
    )
    filters = config["technical_filter"]
    prepared_rows, preparation = prepare_candidate_rows(
        base_rows + source_rows,
        artifact_root=output_dir,
        minimum_width=filters["minimum_width"],
        minimum_height=filters["minimum_height"],
        near_duplicate_hamming_distance=filters["near_duplicate_hamming_distance"],
    )
    write_rows(manifest_path, prepared_rows)
    audit = audit_manifest(manifest_path)
    targets = config["targets"]
    coverage = coverage_decision(
        preparation,
        release_floor_total=targets["release_floor_total"],
        release_floor_per_class=targets["release_floor_per_class"],
        preferred_per_class=targets["preferred_per_class"],
        not_target_floor=targets["not_target_floor"],
    )
    sources = [
        item
        for item in prior_report["sources"]
        if item["source"] != "inaturalist"
    ] + [source_report]
    refreshed = {
        **prior_report,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "sources": sources,
        "preparation": preparation,
        "coverage": coverage,
        "manifest_audit": audit,
    }
    report_path.write_text(
        json.dumps(refreshed, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = {
        "inaturalist": {
            "api_results": source_report["api_results"],
            "eligible_photo_results": source_report["eligible_photo_results"],
            "downloaded": source_report["downloaded"],
            "failures": len(source_report["failures"]),
        },
        "candidate_unique": preparation["candidate_unique"],
        "coverage": coverage,
        "audit_errors": audit["error_count"],
        "audit_warnings": audit["warning_count"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if audit["ok"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
