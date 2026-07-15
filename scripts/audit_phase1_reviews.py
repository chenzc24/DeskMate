"""Audit human review decisions without freezing or accepting rows automatically."""

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

from deskmate_baseline.review import audit_review_queue  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs" / "baseline_phase1_data.toml"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "data" / "downloads" / "phase1_candidates" / "source_manifest.csv",
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
        "--output",
        type=Path,
        default=ROOT
        / "data"
        / "downloads"
        / "phase1_candidates"
        / "review_batches"
        / "review_audit.json",
    )
    args = parser.parse_args()
    with args.config.open("rb") as handle:
        config = tomllib.load(handle)
    targets = config["targets"]
    report = audit_review_queue(
        manifest_path=args.manifest,
        queue_path=args.queue,
        second_reviewer_required_for=set(config["review"]["second_reviewer_required_for"]),
        release_floor_total=targets["release_floor_total"],
        release_floor_per_class=targets["release_floor_per_class"],
        preferred_per_class=targets["preferred_per_class"],
        not_target_floor=targets["not_target_floor"],
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["ready_to_freeze_split"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
