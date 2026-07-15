"""Measure raw base-model GPU latency without claiming Cat Census accuracy."""

from __future__ import annotations

import json
import statistics
import time
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round((len(ordered) - 1) * fraction))))
    return ordered[index]


def main() -> int:
    import torch
    from ultralytics import YOLO

    config = tomllib.loads((ROOT / "configs" / "baseline_inference.toml").read_text(encoding="utf-8"))
    benchmark = config["benchmark"]
    model = YOLO(str(ROOT / config["checkpoint"]), task="classify")
    image = str(ROOT / benchmark["smoke_image"])
    kwargs = {"source": image, "imgsz": config["imgsz"], "device": config["device"], "verbose": False}
    for _ in range(int(benchmark["warmup_iterations"])):
        model.predict(**kwargs)
    torch.cuda.synchronize()
    latencies = []
    for _ in range(int(benchmark["measured_iterations"])):
        start = time.perf_counter_ns()
        result = model.predict(**kwargs)[0]
        torch.cuda.synchronize()
        latencies.append((time.perf_counter_ns() - start) / 1_000_000)
    report = {
        "schema_version": 1,
        "evidence_role": "raw_base_model_latency_only",
        "cat_census_accuracy_evidence": False,
        "iterations": len(latencies),
        "mean_ms": statistics.fmean(latencies),
        "p50_ms": percentile(latencies, 0.50),
        "p95_ms": percentile(latencies, 0.95),
        "throughput_fps_from_mean": 1000.0 / statistics.fmean(latencies),
        "probs_present": result.probs is not None,
        "boxes_present": result.boxes is not None,
        "gpu": torch.cuda.get_device_name(0),
        "includes_capture_or_ui": False,
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
