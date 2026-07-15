"""Acquire and technically prepare Phase 1 candidates without accepting them."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from deskmate_baseline.data.dataset_prep import (  # noqa: E402
    coverage_decision,
    prepare_candidate_rows,
    write_rows,
)
from deskmate_baseline.domain.manifest import audit_manifest  # noqa: E402
from deskmate_baseline.data.source_pilot import (  # noqa: E402
    run_commons_pair,
    run_gbif_pallas,
    run_inaturalist_pallas,
    run_oxford_pilot,
)


def config_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs" / "baseline_phase1_data.toml"
    )
    args = parser.parse_args()
    with args.config.open("rb") as handle:
        config = tomllib.load(handle)

    output_dir = ROOT / config["paths"]["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    user_agent = config["user_agent"]
    timeout = config["network"]["request_timeout_seconds"]
    commons = config["commons"]
    rows: list[dict[str, str]] = []
    source_reports: list[dict[str, object]] = []

    for label, category in commons["target_categories"].items():
        print(f"PHASE1 commons target/{label}: start", file=sys.stderr, flush=True)
        source_rows, source_report = run_commons_pair(
            api_url=commons["api_url"],
            category=category,
            label=label,
            limit=commons["limit_per_target_category"],
            max_depth=config["network"]["commons_max_depth"],
            output_dir=output_dir,
            user_agent=user_agent,
            timeout=timeout,
        )
        rows.extend(source_rows)
        source_reports.append(source_report)
        print(
            f"PHASE1 commons target/{label}: downloaded={source_report['downloaded']}",
            file=sys.stderr,
            flush=True,
        )

    for group, category in commons["supplemental_target_categories"].items():
        print(f"PHASE1 commons supplemental/{group}: start", file=sys.stderr, flush=True)
        source_rows, source_report = run_commons_pair(
            api_url=commons["api_url"],
            category=category,
            label="pallas",
            limit=commons["limit_per_supplemental_target_category"],
            max_depth=config["network"]["commons_max_depth"],
            output_dir=output_dir,
            user_agent=user_agent,
            timeout=timeout,
            group_name=group,
        )
        rows.extend(source_rows)
        source_reports.append(source_report)
        print(
            f"PHASE1 commons supplemental/{group}: downloaded={source_report['downloaded']}",
            file=sys.stderr,
            flush=True,
        )

    inat = config["inaturalist"]
    print("PHASE1 inaturalist/pallas: start", file=sys.stderr, flush=True)
    source_rows, source_report = run_inaturalist_pallas(
        api_url=inat["api_url"],
        taxon_id=inat["taxon_id"],
        label=inat["label"],
        allowed_licenses=set(inat["allowed_photo_licenses"]),
        limit=inat["limit"],
        output_dir=output_dir,
        user_agent=user_agent,
        timeout=timeout,
        max_pages=inat["max_api_pages"],
    )
    rows.extend(source_rows)
    source_reports.append(source_report)
    print(
        f"PHASE1 inaturalist/pallas: downloaded={source_report['downloaded']}",
        file=sys.stderr,
        flush=True,
    )

    gbif = config["gbif"]
    print("PHASE1 gbif/pallas: start", file=sys.stderr, flush=True)
    source_rows, source_report = run_gbif_pallas(
        api_url=gbif["api_url"],
        scientific_name=gbif["scientific_name"],
        label=gbif["label"],
        allowed_licenses=set(gbif["allowed_media_licenses"]),
        limit=gbif["limit"],
        output_dir=output_dir,
        user_agent=user_agent,
        timeout=timeout,
    )
    rows.extend(source_rows)
    source_reports.append(source_report)
    print(
        f"PHASE1 gbif/pallas: downloaded={source_report['downloaded']}",
        file=sys.stderr,
        flush=True,
    )

    for group, category in commons["negative_categories"].items():
        print(f"PHASE1 not_target/{group}: start", file=sys.stderr, flush=True)
        source_rows, source_report = run_commons_pair(
            api_url=commons["api_url"],
            category=category,
            label="not_target",
            limit=commons["limit_per_negative_category"],
            max_depth=config["network"]["commons_max_depth"],
            output_dir=output_dir,
            user_agent=user_agent,
            timeout=timeout,
            group_name=group,
        )
        rows.extend(source_rows)
        source_reports.append(source_report)
        print(
            f"PHASE1 not_target/{group}: downloaded={source_report['downloaded']}",
            file=sys.stderr,
            flush=True,
        )

    oxford = config["oxford_iiit_pet"]
    print("PHASE1 oxford: extract all configured labels", file=sys.stderr, flush=True)
    oxford_rows, oxford_report = run_oxford_pilot(
        archive_url=oxford["images_archive_url"],
        page_url=oxford["page_url"],
        labels=oxford["labels"],
        limit=None,
        license_name=oxford["license_name"],
        license_url=oxford["license_url"],
        attribution=oxford["attribution"],
        output_dir=output_dir,
        user_agent=user_agent,
        timeout=config["network"]["archive_timeout_seconds"],
        archive_path=ROOT / config["paths"]["phase0_oxford_archive"],
    )
    rows.extend(oxford_rows)

    filters = config["technical_filter"]
    prepared_rows, preparation = prepare_candidate_rows(
        rows,
        artifact_root=output_dir,
        minimum_width=filters["minimum_width"],
        minimum_height=filters["minimum_height"],
        near_duplicate_hamming_distance=filters["near_duplicate_hamming_distance"],
    )
    manifest_path = output_dir / "source_manifest.csv"
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
    full_report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "config": str(args.config),
        "config_sha256": config_sha256(args.config),
        "manifest": str(manifest_path),
        "sources": source_reports,
        "oxford": oxford_report,
        "preparation": preparation,
        "coverage": coverage,
        "manifest_audit": audit,
        "deferred_robot_evidence": config["deferred_robot_evidence"],
    }
    report_path = output_dir / "candidate_report.full.json"
    report_path.write_text(
        json.dumps(full_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = {
        "manifest": str(manifest_path),
        "report": str(report_path),
        "raw_rows": preparation["raw_rows"],
        "manifest_rows": preparation["manifest_rows"],
        "candidate_unique": preparation["candidate_unique"],
        "rejected": preparation["rejected"],
        "coverage": coverage,
        "audit_errors": audit["error_count"],
        "audit_warnings": audit["warning_count"],
        "exact_duplicate_clusters": len(preparation["exact_duplicate_clusters"]),
        "near_duplicate_clusters": len(preparation["near_duplicate_clusters"]),
        "automatic_acceptance": False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if audit["ok"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
