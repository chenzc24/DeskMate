"""Guard and execute one development-only provisional B-M01 training run."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
import time
import tomllib
from pathlib import Path
from typing import Any, Callable, Mapping


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from deskmate_baseline.domain.contracts import INTERNAL_LABELS  # noqa: E402
from deskmate_baseline.perception.inference import canonical_index_mapping  # noqa: E402


CLASS_DIRS = {label: f"{index}_{label}" for index, label in enumerate(INTERNAL_LABELS)}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def project_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_config(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        config = tomllib.load(handle)
    if int(config.get("schema_version", 0)) != 1:
        raise ValueError("unsupported provisional training config schema")
    if tuple(config["dataset"]["labels"]) != INTERNAL_LABELS:
        raise ValueError("provisional class order is not canonical")
    if config["model"]["task"] != "classify":
        raise ValueError("B-M01 provisional task must be classify")
    if abs(sum(float(config["split"][name]) for name in ("train", "val_select", "val_cal")) - 1) > 1e-9:
        raise ValueError("split ratios must sum to one")
    return config


def validate_dataset_layout(dataset_root: Path) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for split in ("train", "val", "val_cal"):
        split_root = dataset_root / split
        if not split_root.is_dir():
            raise FileNotFoundError(split_root)
        observed = sorted(path.name for path in split_root.iterdir() if path.is_dir())
        expected = sorted(CLASS_DIRS.values())
        if observed != expected:
            raise ValueError(f"{split} class directories mismatch: {observed}")
        result[split] = {
            label: len(list((split_root / CLASS_DIRS[label]).glob("*")))
            for label in INTERNAL_LABELS
        }
        if any(count <= 0 for count in result[split].values()):
            raise ValueError(f"{split} contains an empty class")
    return result


def build_plan(config_path: Path, seed: int | None = None) -> dict[str, Any]:
    config = load_config(config_path)
    dataset = config["dataset"]
    model = config["model"]
    training = config["training"]
    selected_seed = int(seed if seed is not None else training["initial_seed"])
    if selected_seed not in [int(value) for value in training["comparison_seeds"]]:
        raise ValueError("seed is not in the provisional comparison set")
    split_manifest = project_path(dataset["split_manifest"])
    split_report = project_path(dataset["split_report"])
    dataset_root = project_path(dataset["dataset_root"])
    weights = project_path(model["weights"])
    report = json.loads(split_report.read_text(encoding="utf-8"))
    if report.get("provisional_training_data_ready") is not True:
        raise RuntimeError("provisional dataset is not ready")
    if report.get("official_gate_b1_ready") is not False:
        raise RuntimeError("provisional guard expected official Gate B1 to remain false")
    if report.get("risk_scope") != "development_only_not_final_release":
        raise RuntimeError("provisional risk scope is missing")
    if sha256_file(split_manifest) != report.get("manifest_sha256"):
        raise RuntimeError("provisional split manifest checksum mismatch")
    expected_weight_hash = str(model["expected_sha256"]).casefold()
    if sha256_file(weights) != expected_weight_hash:
        raise RuntimeError("base weight checksum mismatch")
    layout = validate_dataset_layout(dataset_root)
    project = project_path(training["project"])
    run_name = f"b-m01-provisional-bd01-oneview-seed-{selected_seed}"
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
        "seed": selected_seed,
        "project": str(project),
        "name": run_name,
        "exist_ok": False,
        **config["augmentation"],
    }
    return {
        "schema_version": 1,
        "model_id": model["id"],
        "scope": "development_only_not_final_release",
        "official_gate_b1_ready": False,
        "weights": str(weights),
        "weights_sha256": expected_weight_hash,
        "config_path": str(config_path),
        "config_sha256": sha256_file(config_path),
        "split_manifest": str(split_manifest),
        "split_manifest_sha256": report["manifest_sha256"],
        "split_report": str(split_report),
        "class_order": list(INTERNAL_LABELS),
        "layout": layout,
        "kwargs": kwargs,
        "expected_run_dir": str(project / run_name),
        "execution_authorized": True,
    }


def parse_results_csv(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [{key.strip(): (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]
    if not rows:
        raise ValueError("training results.csv is empty")
    top1_key = next((key for key in rows[0] if "accuracy_top1" in key), None)
    top5_key = next((key for key in rows[0] if "accuracy_top5" in key), None)
    if top1_key is None:
        raise ValueError("training results do not contain top-1 accuracy")
    best_index = max(range(len(rows)), key=lambda index: float(rows[index][top1_key]))
    best = rows[best_index]
    return {
        "epochs_completed": len(rows),
        "best_epoch_zero_based": int(float(best.get("epoch", best_index))),
        "best_val_top1": float(best[top1_key]),
        "best_val_top5": float(best[top5_key]) if top5_key else None,
        "best_row": best,
        "last_row": rows[-1],
    }


def execute(
    plan: dict[str, Any], *, model_factory: Callable[..., Any] | None = None
) -> dict[str, Any]:
    if plan.get("execution_authorized") is not True:
        raise RuntimeError("provisional execution is not authorized")
    run_dir = Path(plan["expected_run_dir"])
    if run_dir.exists():
        raise FileExistsError(f"run directory already exists: {run_dir}")
    if model_factory is None:
        from ultralytics import YOLO

        model_factory = YOLO
    started = time.time()
    model = model_factory(plan["weights"], task="classify")
    result = model.train(**plan["kwargs"])
    elapsed = time.time() - started
    save_dir = Path(getattr(result, "save_dir", run_dir))
    results_csv = save_dir / "results.csv"
    best_path = save_dir / "weights" / "best.pt"
    last_path = save_dir / "weights" / "last.pt"
    metrics = parse_results_csv(results_csv)
    for path in (best_path, last_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    verifier = model_factory(str(best_path), task="classify")
    class_mapping = canonical_index_mapping(verifier.names)
    native_names = (
        {int(key): str(value) for key, value in verifier.names.items()}
        if isinstance(verifier.names, Mapping)
        else {index: str(value) for index, value in enumerate(verifier.names)}
    )
    report = {
        "schema_version": 1,
        "status": "PROVISIONAL_TRAINING_COMPLETE",
        "scope": plan["scope"],
        "official_gate_b1_ready": False,
        "model_id": plan["model_id"],
        "elapsed_seconds": elapsed,
        "save_dir": str(save_dir),
        "hardware": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
        },
        "training": metrics,
        "checkpoints": {
            "best": {"path": str(best_path), "sha256": sha256_file(best_path), "bytes": best_path.stat().st_size},
            "last": {"path": str(last_path), "sha256": sha256_file(last_path), "bytes": last_path.stat().st_size},
        },
        "native_names": {str(key): value for key, value in native_names.items()},
        "canonical_index_mapping": list(class_mapping),
        "config_sha256": plan["config_sha256"],
        "split_manifest_sha256": plan["split_manifest_sha256"],
    }
    (save_dir / "provisional_training_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "baseline_training_provisional.toml",
    )
    parser.add_argument("--seed", type=int)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    plan = build_plan(args.config, seed=args.seed)
    if not args.execute:
        print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    report = execute(plan)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
