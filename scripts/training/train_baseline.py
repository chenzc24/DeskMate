from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from deskmate_baseline.experiments.training import build_training_plan, execute_training


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or execute the B-M01 training plan")
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "baseline_training.toml")
    parser.add_argument("--gate-report", type=Path, default=ROOT / "data" / "cat_census" / "split_manifest.report.json")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    plan = build_training_plan(config_path=args.config, seed=args.seed)
    if not args.execute:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0
    execute_training(plan, gate_b1_report=args.gate_report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
