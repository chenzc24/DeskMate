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

from deskmate_baseline.split import (
    GateB1NotReady,
    build_frozen_split,
    materialize_dataset_view,
    write_split_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze the reviewed Baseline split")
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "baseline_training.toml")
    parser.add_argument("--materialize", action="store_true")
    args = parser.parse_args()
    config = tomllib.loads(args.config.read_text(encoding="utf-8"))
    dataset = config["dataset"]
    project_path = lambda value: ROOT / value  # paths in the tracked config are project-relative
    manifest_path = project_path(dataset["source_manifest"])
    queue_path = project_path(dataset["review_queue"])
    try:
        rows, report = build_frozen_split(
            manifest_path=manifest_path,
            queue_path=queue_path,
            second_reviewer_required_for=set(dataset["second_review_required"]),
            release_floor_total=int(dataset["release_floor_total"]),
            release_floor_per_class=int(dataset["release_floor_per_class"]),
            preferred_per_class=int(dataset["preferred_per_class"]),
            not_target_floor=int(dataset["not_target_floor"]),
            seed=int(dataset["seed"]),
            ratios={key: float(value) for key, value in config["split"].items()},
        )
    except GateB1NotReady as exc:
        print(json.dumps({"ready": False, "review_audit": exc.report}, indent=2))
        return 3
    split_manifest = project_path(dataset["split_manifest"])
    write_split_manifest(split_manifest, rows)
    report_path = split_manifest.with_suffix(".report.json")
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.materialize:
        report["materialization"] = materialize_dataset_view(
            rows=rows,
            source_root=manifest_path.parent,
            output_root=project_path(dataset["dataset_root"]),
        )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
