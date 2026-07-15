#!/usr/bin/env python3
"""Build classifier hardening dataset variants from the frozen one-view split."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from deskmate_baseline.experiments.classifier_hardening import (  # noqa: E402
    build_hardening_datasets,
    sha256_file,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "baseline_classifier_hardening.toml",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with args.config.open("rb") as handle:
        config = tomllib.load(handle)
    dataset = config["dataset"]
    output = args.output or ROOT / dataset["output_root"]
    rows = build_hardening_datasets(
        source_root=ROOT / dataset["source_root"],
        output_root=output,
        class_directories=dataset["class_directories"],
        target_train_images_per_class=int(dataset["target_train_images_per_class"]),
        printed_page_labels=dataset["printed_page_labels"],
        variants=dataset["variants"],
        seed=int(config["seed"]),
        printed_page=config["printed_page"],
    )
    counts = Counter((row["variant"], row["split"], row["label"], row["view_kind"]) for row in rows)
    report = {
        "schema_version": 1,
        "status": "CLASSIFIER_HARDENING_DATASET_READY",
        "config_sha256": sha256_file(args.config),
        "manifest_sha256": sha256_file(output / "manifest.csv"),
        "row_count": len(rows),
        "counts": [
            {
                "variant": key[0],
                "split": key[1],
                "label": key[2],
                "view_kind": key[3],
                "count": value,
            }
            for key, value in sorted(counts.items())
        ],
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
