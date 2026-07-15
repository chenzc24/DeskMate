"""Run bounded, traceable source pilots without Selenium."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from deskmate_baseline.source_pilot import (  # noqa: E402
    run_commons_pair,
    run_inaturalist_pallas,
    run_oxford_pilot,
    write_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs" / "baseline_sources.toml"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "data" / "downloads" / "phase0_pilot",
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--only",
        help=(
            "Run one unit: commons:<label>, inaturalist:pallas, "
            "not_target:<group>, or oxford"
        ),
    )
    args = parser.parse_args()

    with args.config.open("rb") as handle:
        config = tomllib.load(handle)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    limit = args.limit or config["pilot"]["download_limit_per_pair"]
    timeout = config["pilot"]["request_timeout_seconds"]
    user_agent = config["user_agent"]

    rows: list[dict[str, str]] = []
    pair_reports: list[dict[str, object]] = []
    for label, category in config["commons"]["categories"].items():
        unit = f"commons:{label}"
        if args.only and args.only != unit:
            continue
        print(f"PILOT commons/{label}: start", file=sys.stderr, flush=True)
        pair_rows, pair_report = run_commons_pair(
            api_url=config["commons"]["api_url"],
            category=category,
            label=label,
            limit=limit,
            max_depth=config["pilot"]["commons_max_depth"],
            output_dir=output_dir,
            user_agent=user_agent,
            timeout=timeout,
        )
        rows.extend(pair_rows)
        pair_reports.append(pair_report)
        print(
            f"PILOT commons/{label}: downloaded={pair_report['downloaded']} "
            f"failures={len(pair_report['failures'])}",
            file=sys.stderr,
            flush=True,
        )

    inat = config["inaturalist"]
    if not args.only or args.only == "inaturalist:pallas":
        print("PILOT inaturalist/pallas: start", file=sys.stderr, flush=True)
        inat_rows, inat_report = run_inaturalist_pallas(
            api_url=inat["api_url"],
            taxon_id=inat["taxon_id"],
            label=inat["label"],
            allowed_licenses=set(inat["allowed_photo_licenses"]),
            limit=limit,
            output_dir=output_dir,
            user_agent=user_agent,
            timeout=timeout,
        )
        rows.extend(inat_rows)
        pair_reports.append(inat_report)
        print(
            f"PILOT inaturalist/pallas: downloaded={inat_report['downloaded']} "
            f"failures={len(inat_report['failures'])}",
            file=sys.stderr,
            flush=True,
        )

    negative = config["not_target"]
    for group, category in negative["commons_categories"].items():
        unit = f"not_target:{group}"
        if args.only and args.only != unit:
            continue
        print(f"PILOT not_target/{group}: start", file=sys.stderr, flush=True)
        negative_rows, negative_report = run_commons_pair(
            api_url=config["commons"]["api_url"],
            category=category,
            label="not_target",
            limit=limit,
            max_depth=config["pilot"]["commons_max_depth"],
            output_dir=output_dir,
            user_agent=user_agent,
            timeout=timeout,
            group_name=group,
        )
        rows.extend(negative_rows)
        pair_reports.append(negative_report)
        print(
            f"PILOT not_target/{group}: downloaded={negative_report['downloaded']} "
            f"failures={len(negative_report['failures'])}",
            file=sys.stderr,
            flush=True,
        )
    oxford = config["oxford_iiit_pet"]
    run_oxford = not args.only or args.only == "oxford"
    oxford_report = None
    if run_oxford:
        print("PILOT oxford: verified archive and bounded extraction", file=sys.stderr, flush=True)
        oxford_rows, oxford_report = run_oxford_pilot(
            archive_url=oxford["images_archive_url"],
            page_url=oxford["page_url"],
            labels=oxford["labels"],
            limit=oxford["pilot_count_per_label"],
            license_name=oxford["license_name"],
            license_url=oxford["license_url"],
            attribution=oxford["attribution"],
            output_dir=output_dir,
            user_agent=user_agent,
            timeout=config["pilot"]["archive_timeout_seconds"],
        )
        rows.extend(oxford_rows)

    suffix = "" if not args.only else "_" + args.only.replace(":", "_")
    manifest_path = output_dir / f"pilot_manifest{suffix}.csv"
    report_path = output_dir / f"pilot_report{suffix}.json"
    write_manifest(manifest_path, rows)
    report = {
        "schema_version": 1,
        "limit_per_pair": limit,
        "unit": args.only or "all",
        "manifest": str(manifest_path),
        "rows": len(rows),
        "pairs": pair_reports,
        "oxford": oxford_report,
        "selenium_used": False,
        "automatic_acceptance": False,
        "complete_pairs": sum(bool(item["complete"]) for item in pair_reports)
        + (
            sum(bool(item["complete"]) for item in oxford_report["labels"].values())
            if oxford_report
            else 0
        ),
        "required_pairs": len(pair_reports)
        + (len(oxford_report["labels"]) if oxford_report else 0),
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["complete_pairs"] == report["required_pairs"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
