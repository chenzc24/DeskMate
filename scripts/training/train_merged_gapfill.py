from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_results(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [{key.strip(): value.strip() for key, value in row.items()} for row in csv.DictReader(handle)]
    top1 = next(key for key in rows[0] if "accuracy_top1" in key)
    top5 = next(key for key in rows[0] if "accuracy_top5" in key)
    best = max(rows, key=lambda row: float(row[top1]))
    return {
        "epochs_completed": len(rows),
        "best_epoch_zero_based": int(float(best["epoch"])),
        "best_top1": float(best[top1]),
        "best_top5": float(best[top5]),
        "best_val_loss": float(best["val/loss"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs/baseline_training_merged_gapfill.toml")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    with args.config.open("rb") as handle:
        config = tomllib.load(handle)
    model_cfg = config["model"]
    dataset_cfg = config["dataset"]
    training = config["training"]
    weights = ROOT / model_cfg["weights"]
    dataset_root = ROOT / dataset_cfg["root"]
    manifest = ROOT / dataset_cfg["manifest"]
    dataset_report = json.loads((ROOT / dataset_cfg["report"]).read_text(encoding="utf-8"))
    if sha256_file(weights) != model_cfg["expected_sha256"]:
        raise RuntimeError("base weights checksum mismatch")
    if dataset_report["status"] not in {
        "MERGED_DATASET_READY",
        "NO_OTHER_CAT_DATASET_READY",
        "MACHINE_VIEW_MERGED_DATASET_READY",
    }:
        raise RuntimeError("merged dataset is not ready")
    if sha256_file(manifest) != dataset_report["manifest_sha256"]:
        raise RuntimeError("merged manifest checksum mismatch")
    layout = {
        split: {
            label: len(list((dataset_root / split / directory).glob("*")))
            for label, directory in zip(dataset_cfg["labels"], dataset_cfg["class_directories"])
        }
        for split in ("train", "val", "val_cal")
    }
    if layout != dataset_report["final_counts"]:
        raise RuntimeError(f"dataset layout differs from report: {layout}")
    run_root = ROOT / training["project"]
    run_dir = run_root / training["name"]
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
        "seed": int(config["seed"]),
        "project": str(run_root),
        "name": training["name"],
        "exist_ok": False,
        **config["augmentation"],
    }
    plan = {
        "model_id": model_cfg["id"],
        "weights": str(weights),
        "weights_sha256": sha256_file(weights),
        "dataset_root": str(dataset_root),
        "manifest_sha256": sha256_file(manifest),
        "layout": layout,
        "run_dir": str(run_dir),
        "kwargs": kwargs,
    }
    if not args.execute:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    if run_dir.exists():
        raise FileExistsError(run_dir)
    from ultralytics import YOLO

    started = time.time()
    result = YOLO(str(weights), task="classify").train(**kwargs)
    elapsed = time.time() - started
    actual_run = Path(result.save_dir)
    best = actual_run / "weights" / "best.pt"
    last = actual_run / "weights" / "last.pt"
    if not best.is_file() or not last.is_file():
        raise FileNotFoundError("training checkpoints are incomplete")
    names = YOLO(str(best), task="classify").names
    report = {
        "schema_version": 1,
        "status": "MERGED_GAPFILL_TRAINING_COMPLETE",
        "model_id": model_cfg["id"],
        "elapsed_seconds": elapsed,
        "dataset_root": str(dataset_root),
        "manifest_sha256": sha256_file(manifest),
        "layout": layout,
        "training": parse_results(actual_run / "results.csv"),
        "best": {"path": str(best), "sha256": sha256_file(best), "bytes": best.stat().st_size},
        "last": {"path": str(last), "sha256": sha256_file(last), "bytes": last.stat().st_size},
        "native_names": names,
    }
    (actual_run / "merged_gapfill_training_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
