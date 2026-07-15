#!/usr/bin/env python3
"""Average compatible B-M01 checkpoints into single-model candidates."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tomllib
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from deskmate_baseline.perception.inference import canonical_index_mapping  # noqa: E402


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    config_path = ROOT / "configs/baseline_classifier_soups.toml"
    with config_path.open("rb") as handle:
        config = tomllib.load(handle)
    source_paths = {name: ROOT / value for name, value in config["sources"].items()}
    checkpoints = {
        name: torch.load(path, map_location="cpu", weights_only=False)
        for name, path in source_paths.items()
    }
    states = {name: checkpoint["model"].float().state_dict() for name, checkpoint in checkpoints.items()}
    keys = tuple(next(iter(states.values())).keys())
    if any(tuple(state.keys()) != keys for state in states.values()):
        raise RuntimeError("checkpoint state keys differ")
    output = ROOT / config["output"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": 1,
        "status": "SINGLE_MODEL_WEIGHT_SOUPS_READY",
        "sources": {
            name: {"path": str(path.relative_to(ROOT)), "sha256": sha256_file(path)}
            for name, path in source_paths.items()
        },
        "soups": {},
    }
    from ultralytics import YOLO

    for soup_name, weights in config["soups"].items():
        coefficients = {name: float(weights[name]) for name in source_paths}
        if abs(sum(coefficients.values()) - 1.0) > 1e-9 or any(
            value < 0 for value in coefficients.values()
        ):
            raise ValueError(f"invalid soup coefficients: {soup_name}")
        checkpoint = copy.deepcopy(checkpoints["current"])
        model = checkpoint["model"].float()
        averaged = {}
        for key in keys:
            tensors = [states[name][key] for name in source_paths]
            if tensors[0].is_floating_point():
                value = sum(
                    tensors[index] * coefficients[name]
                    for index, name in enumerate(source_paths)
                )
            else:
                # BatchNorm counters do not affect inference; retain the current model's value.
                value = tensors[0]
            averaged[key] = value
        model.load_state_dict(averaged, strict=True)
        checkpoint["model"] = model.half()
        checkpoint["ema"] = None
        checkpoint["optimizer"] = None
        checkpoint["scaler"] = None
        checkpoint["epoch"] = -1
        checkpoint["best_fitness"] = None
        destination = output / f"{soup_name}.pt"
        torch.save(checkpoint, destination)
        verifier = YOLO(str(destination), task="classify")
        canonical_index_mapping(verifier.names)
        report["soups"][soup_name] = {
            "path": str(destination.relative_to(ROOT)),
            "sha256": sha256_file(destination),
            "coefficients": coefficients,
        }
    (output / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
