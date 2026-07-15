"""Interpolate the frozen target-five model with the machine-data fine-tune."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import tomllib
from pathlib import Path

import torch

from deskmate_baseline.perception.target_inference import target_index_mapping


ROOT = Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs/baseline_target5_machine_soups.toml",
    )
    args = parser.parse_args()
    with args.config.open("rb") as handle:
        config = tomllib.load(handle)
    base_path = (ROOT / config["sources"]["base"]).resolve()
    adapted_path = (ROOT / config["sources"]["machine_finetuned"]).resolve()
    base = torch.load(base_path, map_location="cpu", weights_only=False)
    adapted = torch.load(adapted_path, map_location="cpu", weights_only=False)
    base_state = base["model"].float().state_dict()
    adapted_state = adapted["model"].float().state_dict()
    keys = tuple(base_state)
    if keys != tuple(adapted_state):
        raise RuntimeError("checkpoint state keys differ")
    output = (ROOT / config["output"]["directory"]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": 1,
        "status": "TARGET5_MACHINE_WEIGHT_SOUPS_READY",
        "sources": {
            "base": {"path": str(base_path), "sha256": sha256_file(base_path)},
            "machine_finetuned": {
                "path": str(adapted_path),
                "sha256": sha256_file(adapted_path),
            },
        },
        "candidates": {},
    }
    from ultralytics import YOLO

    for name, alpha_value in config["alphas"].items():
        alpha = float(alpha_value)
        if not 0.0 < alpha <= 1.0:
            raise ValueError(f"invalid machine coefficient: {name}={alpha}")
        checkpoint = copy.deepcopy(base)
        model = checkpoint["model"].float()
        merged = {
            key: (
                base_state[key] * (1.0 - alpha) + adapted_state[key] * alpha
                if base_state[key].is_floating_point()
                else base_state[key]
            )
            for key in keys
        }
        model.load_state_dict(merged, strict=True)
        checkpoint["model"] = model.half()
        checkpoint["ema"] = None
        checkpoint["optimizer"] = None
        checkpoint["scaler"] = None
        checkpoint["epoch"] = -1
        checkpoint["best_fitness"] = None
        destination = output / f"target5_machine_alpha_{alpha:.2f}.pt"
        torch.save(checkpoint, destination)
        target_index_mapping(YOLO(str(destination), task="classify").names)
        report["candidates"][name] = {
            "machine_coefficient": alpha,
            "base_coefficient": 1.0 - alpha,
            "path": str(destination),
            "sha256": sha256_file(destination),
        }
    (output / "build_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
