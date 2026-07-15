from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from deskmate_baseline.evaluation import (  # noqa: E402
    evaluate_predictions,
    fit_temperature,
    prediction_manifest_sha256,
    read_prediction_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "baseline_evaluation.toml")
    parser.add_argument("--fit-temperature", action="store_true")
    parser.add_argument("--temperature", type=float, default=1.0)
    args = parser.parse_args()
    config = tomllib.loads(args.config.read_text(encoding="utf-8"))
    rows = read_prediction_manifest(args.manifest)
    calibration = None
    temperature = args.temperature
    if args.fit_temperature:
        section = config["temperature"]
        calibration = fit_temperature(
            rows,
            minimum=float(section["minimum"]),
            maximum=float(section["maximum"]),
            steps=int(section["steps"]),
        )
        temperature = calibration["temperature"]
    report = evaluate_predictions(rows, temperature=temperature, ece_bins=int(config["ece_bins"]))
    report["prediction_manifest_sha256"] = prediction_manifest_sha256(args.manifest)
    report["calibration"] = calibration
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
