#!/usr/bin/env python3
"""Train one deterministic classifier-hardening candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from deskmate_baseline.domain.contracts import INTERNAL_LABELS  # noqa: E402
from deskmate_baseline.perception.inference import canonical_index_mapping  # noqa: E402


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def count_layout(root: Path, class_directories: list[str]) -> dict[str, dict[str, int]]:
    return {
        split: {
            label: len(list((root / split / directory).glob("*")))
            for label, directory in zip(INTERNAL_LABELS, class_directories)
        }
        for split in ("train", "val", "val_cal")
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("variant", choices=("balanced_oneview", "balanced_print"))
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "baseline_classifier_hardening.toml",
    )
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    with args.config.open("rb") as handle:
        config = tomllib.load(handle)
    if tuple(config["dataset"]["labels"]) != INTERNAL_LABELS:
        raise ValueError("class order is not canonical")
    weights = ROOT / config["model"]["weights"]
    if sha256_file(weights) != config["model"]["expected_sha256"]:
        raise RuntimeError("base checkpoint checksum mismatch")
    dataset_root = ROOT / config["dataset"]["output_root"] / args.variant
    layout = count_layout(dataset_root, config["dataset"]["class_directories"])
    expected = int(config["dataset"]["target_train_images_per_class"])
    if set(layout["train"].values()) != {expected}:
        raise RuntimeError(f"training layout is not balanced: {layout['train']}")
    report = json.loads(
        (ROOT / config["dataset"]["output_root"] / "report.json").read_text(
            encoding="utf-8"
        )
    )
    if report["config_sha256"] != sha256_file(args.config):
        raise RuntimeError("dataset and training config checksums differ")
    training = config["training"]
    seed = int(config["seed"])
    run_name = f"b-m01-{args.variant}-seed-{seed}"
    run_root = ROOT / training["project"]
    kwargs = {
        "data": str(dataset_root),
        "epochs": int(training["epochs"]),
        "imgsz": int(training["imgsz"]),
        "batch": int(training["batch"]),
        "workers": int(training["workers"]),
        "patience": int(training["patience"]),
        "device": training["device"],
        "amp": bool(training["amp"]),
        "deterministic": bool(training["deterministic"]),
        "cache": bool(training["cache"]),
        "optimizer": training["optimizer"],
        "seed": seed,
        "project": str(run_root),
        "name": run_name,
        "exist_ok": False,
        **config["augmentation"],
    }
    plan = {
        "variant": args.variant,
        "weights": str(weights),
        "weights_sha256": sha256_file(weights),
        "dataset_root": str(dataset_root),
        "dataset_manifest_sha256": report["manifest_sha256"],
        "layout": layout,
        "kwargs": kwargs,
        "expected_run_dir": str(run_root / run_name),
    }
    if not args.execute:
        print(json.dumps(plan, indent=2))
        return 0
    from ultralytics import YOLO

    started = time.time()
    model = YOLO(str(weights), task="classify")
    result = model.train(**kwargs)
    elapsed = time.time() - started
    run_dir = Path(result.save_dir)
    best = run_dir / "weights" / "best.pt"
    last = run_dir / "weights" / "last.pt"
    if not best.is_file() or not last.is_file():
        raise FileNotFoundError("training checkpoints are incomplete")
    verifier = YOLO(str(best), task="classify")
    canonical_index_mapping(verifier.names)
    completed = {
        "schema_version": 1,
        "status": "CLASSIFIER_HARDENING_TRAINING_COMPLETE",
        "variant": args.variant,
        "elapsed_seconds": elapsed,
        "layout": layout,
        "base_weights_sha256": sha256_file(weights),
        "dataset_manifest_sha256": report["manifest_sha256"],
        "best": {"path": str(best), "sha256": sha256_file(best)},
        "last": {"path": str(last), "sha256": sha256_file(last)},
    }
    (run_dir / "hardening_training_report.json").write_text(
        json.dumps(completed, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(completed, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
