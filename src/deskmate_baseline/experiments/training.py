"""Pinned B-M01 training-plan generation with explicit execution authority."""

from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path
from typing import Any

from ..domain.contracts import INTERNAL_LABELS


def load_training_config(path: Path) -> dict[str, Any]:
    config = tomllib.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != 1:
        raise ValueError("unsupported training config schema")
    if tuple(config["dataset"]["labels"]) != INTERNAL_LABELS:
        raise ValueError("training class order does not match canonical labels")
    if config["model"]["task"] != "classify":
        raise ValueError("B-M01 must use the classification task")
    ratios = config["split"]
    if abs(sum(float(ratios[name]) for name in ("train", "val_select", "val_cal")) - 1) > 1e-9:
        raise ValueError("training split ratios must sum to one")
    return config


def build_training_plan(
    *, config_path: Path, dataset_root: Path | None = None, seed: int | None = None
) -> dict[str, Any]:
    config = load_training_config(config_path)
    root = config_path.resolve().parent.parent
    training = config["training"]
    model = config["model"]
    selected_seed = int(seed if seed is not None else training["initial_seed"])
    if selected_seed not in [int(value) for value in training["comparison_seeds"]]:
        raise ValueError("seed is not one of the frozen comparison seeds")
    data_path = dataset_root or root / config["dataset"]["dataset_root"]
    kwargs = {
        "data": str(data_path),
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
        "seed": selected_seed,
        "project": str(root / training["project"]),
        "name": f"b-m01-seed-{selected_seed}",
        **config["augmentation"],
    }
    return {
        "schema_version": 1,
        "model_id": model["id"],
        "task": model["task"],
        "weights": str(root / model["weights"]),
        "class_order": list(INTERNAL_LABELS),
        "kwargs": kwargs,
        "execution_authorized": False,
    }


def execute_training(plan: dict[str, Any], *, gate_b1_report: Path) -> Any:
    gate = json.loads(gate_b1_report.read_text(encoding="utf-8"))
    if gate.get("ready") is not True:
        raise RuntimeError("Gate B1 report is not ready; training refused")
    dataset_root = Path(plan["kwargs"]["data"])
    if not (dataset_root / "train").is_dir() or not (dataset_root / "val").is_dir():
        raise RuntimeError("materialized train/val directories are missing")
    weights = Path(plan["weights"])
    if not weights.is_file():
        raise RuntimeError(f"base weights missing: {weights}")
    from ultralytics import YOLO

    model = YOLO(str(weights), task="classify")
    return model.train(**plan["kwargs"])


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
