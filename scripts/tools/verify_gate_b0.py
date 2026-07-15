"""Generate a fail-closed, machine-readable Baseline Gate B0 audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from deskmate_baseline.domain.contracts import INTERNAL_LABELS, REPORTABLE_LABELS  # noqa: E402
from deskmate_baseline.domain.manifest import audit_manifest  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check(check_id: str, passed: bool, evidence: Any) -> dict[str, Any]:
    return {"id": check_id, "passed": bool(passed), "evidence": evidence}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs" / "baseline_phase0.toml"
    )
    parser.add_argument(
        "--sources", type=Path, default=ROOT / "configs" / "baseline_sources.toml"
    )
    parser.add_argument(
        "--review", type=Path, default=ROOT / "configs" / "phase0_pilot_review.toml"
    )
    parser.add_argument(
        "--pilot-manifest",
        type=Path,
        default=ROOT / "data" / "downloads" / "phase0_pilot" / "pilot_manifest.csv",
    )
    parser.add_argument(
        "--pilot-report",
        type=Path,
        default=ROOT / "data" / "downloads" / "phase0_pilot" / "pilot_report.json",
    )
    parser.add_argument(
        "--skeleton-report",
        type=Path,
        default=ROOT / "data" / "downloads" / "phase0_pilot" / "skeleton_smoke_report.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs" / "evaluation" / "BASELINE_PHASE0_B0_REPORT.json",
    )
    args = parser.parse_args()

    with args.config.open("rb") as handle:
        config = tomllib.load(handle)
    with args.sources.open("rb") as handle:
        sources = tomllib.load(handle)
    with args.review.open("rb") as handle:
        review = tomllib.load(handle)
    pilot_report = json.loads(args.pilot_report.read_text(encoding="utf-8"))
    skeleton = json.loads(args.skeleton_report.read_text(encoding="utf-8"))
    manifest_report = audit_manifest(args.pilot_manifest)

    test_run = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    compile_run = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", "src", "tests", "scripts"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    internal_labels = tuple(config["labels"]["internal"])
    reportable_labels = tuple(config["labels"]["reportable"])
    review_pairs = review["pairs"]
    pair_keys = {
        (pair["source_kind"], pair["label"], pair.get("source_group", ""))
        for pair in review_pairs
    }
    required_pair_keys = {
        ("wikimedia_commons", label, "") for label in REPORTABLE_LABELS
    } | {
        ("inaturalist", "pallas", ""),
        *(("oxford_iiit_pet", label, "") for label in sources["oxford_iiit_pet"]["labels"]),
        *(("wikimedia_commons", "not_target", group) for group in sources["not_target"]["commons_categories"]),
    }
    pilot_limit = config["source_pilot"]["minimum_per_source_class"]
    expected_rows = len(required_pair_keys) * pilot_limit
    oxford_labels = pilot_report["oxford"]["labels"]
    negative_groups = set(sources["not_target"]["commons_categories"])
    pilot_negative_groups = {
        item.get("group", "")
        for item in pilot_report["pairs"]
        if item["label"] == "not_target" and item["source"] == "wikimedia_commons"
    }
    review_negative_groups = {
        pair.get("source_group", "")
        for pair in review_pairs
        if pair["label"] == "not_target"
    }
    runtime_contracts = skeleton["contracts"]
    robot = config["robot"]

    checks = [
        check(
            "labels_and_task_contract",
            internal_labels == INTERNAL_LABELS and reportable_labels == REPORTABLE_LABELS,
            {"internal": internal_labels, "reportable": reportable_labels},
        ),
        check(
            "pilot_manifest_provenance",
            manifest_report["ok"]
            and manifest_report["rows"] == expected_rows
            and manifest_report["quarantine_rows"] == expected_rows,
            {
                "rows": manifest_report["rows"],
                "quarantine_rows": manifest_report["quarantine_rows"],
                "errors": manifest_report["error_count"],
                "candidate_unique": manifest_report["candidate_unique"],
            },
        ),
        check(
            "traceable_source_pairs",
            pilot_report["complete_pairs"]
            == pilot_report["required_pairs"]
            == len(required_pair_keys),
            {
                "complete_pairs": pilot_report["complete_pairs"],
                "required_pairs": pilot_report["required_pairs"],
                "selenium_used": pilot_report["selenium_used"],
            },
        ),
        check(
            "single_review_risk_triage",
            pair_keys == required_pair_keys
            and not review["acceptance_authority"]
            and all(
                pair["downloaded"] >= pilot_limit
                and 0 <= pair["visually_usable"] <= pair["downloaded"]
                and pair["label_error_count"] >= 0
                and pair["license_missing_count"] >= 0
                and pair["duplicate_risk_count"] >= 0
                for pair in review_pairs
            ),
            {
                "reviewed_pairs": len(review_pairs),
                "visually_usable": {
                    ":".join(
                        part
                        for part in (
                            pair["source_kind"],
                            pair["label"],
                            pair.get("source_group", ""),
                        )
                        if part
                    ): pair["visually_usable"]
                    for pair in review_pairs
                },
                "acceptance_authority": review["acceptance_authority"],
            },
        ),
        check(
            "oxford_image_pilot",
            bool(pilot_report["oxford"]["image_pilot_complete"])
            and set(oxford_labels) == set(sources["oxford_iiit_pet"]["labels"])
            and all(item["downloaded"] >= pilot_limit for item in oxford_labels.values())
            and len(pilot_report["oxford"]["archive"]["sha256"]) == 64,
            {
                "archive_bytes": pilot_report["oxford"]["archive"]["bytes"],
                "archive_sha256": pilot_report["oxford"]["archive"]["sha256"],
                "downloaded_by_label": {
                    label: item["downloaded"] for label, item in oxford_labels.items()
                },
                "image_pilot_complete": pilot_report["oxford"]["image_pilot_complete"],
            },
        ),
        check(
            "not_target_source_pilot",
            negative_groups == pilot_negative_groups == review_negative_groups
            and manifest_report["candidate_unique"]["not_target"]
            >= len(negative_groups) * pilot_limit
            and bool(sources["not_target"]["phase1_route"])
            and sources["not_target"]["phase1_floor"]
            == config["source_pilot"]["not_target_floor"],
            {
                "groups": sorted(pilot_negative_groups),
                "candidate_unique": manifest_report["candidate_unique"]["not_target"],
                "required_phase1_floor": config["source_pilot"]["not_target_floor"],
                "phase1_route": sources["not_target"]["phase1_route"],
            },
        ),
        check(
            "deterministic_contract_tests",
            test_run.returncode == 0 and compile_run.returncode == 0,
            {
                "pytest_returncode": test_run.returncode,
                "pytest_summary": test_run.stdout.strip().splitlines()[-1]
                if test_run.stdout.strip()
                else "",
                "compile_returncode": compile_run.returncode,
            },
        ),
        check(
            "bounded_runtime_smoke",
            runtime_contracts["first_job_kind"] == "confirmation"
            and runtime_contracts["second_job_kind"] == "preview"
            and runtime_contracts["preview_console_line"] is None
            and runtime_contracts["duplicate_confirmation_line"] is None
            and runtime_contracts["temporal_size_after_stale"] == 0
            and runtime_contracts["queue_sizes_after_pop"] == [0, 0]
            and not runtime_contracts["motion_enabled"],
            runtime_contracts,
        ),
        check(
            "real_robot_frame",
            bool(skeleton["input"]["real_robot_evidence"]),
            skeleton["input"],
        ),
        check(
            "robot_stream_contract",
            robot["stream_protocol"] != "unknown"
            and bool(robot["stream_endpoint"])
            and robot["orientation"] != "unknown"
            and robot["color_format"] != "unknown",
            robot,
        ),
        check(
            "selenium_disabled_until_phase1_gap_report",
            not pilot_report["selenium_used"],
            {"selenium_used": pilot_report["selenium_used"]},
        ),
        check(
            "calibration_not_frozen_in_phase0",
            not config["calibration"]["thresholds_frozen"]
            and not config["calibration"]["temperature_frozen"],
            config["calibration"],
        ),
    ]
    status = "PASS" if all(item["passed"] for item in checks) else "NOT_PASSED"
    failed = [item["id"] for item in checks if not item["passed"]]

    gpu = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=name,driver_version,memory.total",
            "--format=csv,noheader",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    report = {
        "schema_version": 1,
        "gate": "B0",
        "status": status,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "failed_checks": failed,
        "checks": checks,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "gpu": gpu.stdout.strip() if gpu.returncode == 0 else "unavailable",
        },
        "checksums": {
            "baseline_phase0_config": sha256(args.config),
            "baseline_sources_config": sha256(args.sources),
            "phase0_pilot_review": sha256(args.review),
            "pilot_manifest": sha256(args.pilot_manifest),
            "pilot_report": sha256(args.pilot_report),
            "skeleton_report": sha256(args.skeleton_report),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if status == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
