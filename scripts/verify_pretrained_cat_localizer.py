"""Offline-only smoke of the official COCO cat detector; never admits release use."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from deskmate_baseline.contracts import FramePacket  # noqa: E402
from deskmate_baseline.localization import UltralyticsCatLocalizerBackend  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs" / "baseline_localizer.toml"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs" / "evaluation" / "BASELINE_LOCALIZER_SMOKE.json",
    )
    args = parser.parse_args()
    with args.config.open("rb") as handle:
        config = tomllib.load(handle)

    checkpoint = ROOT / config["checkpoint"]
    backend = UltralyticsCatLocalizerBackend(
        checkpoint=checkpoint,
        model_id=config["model_id"],
        device=config["device"],
        imgsz=config["imgsz"],
        confidence_threshold=config["confidence_threshold"],
        minimum_box_area_ratio=config["minimum_box_area_ratio"],
        maximum_candidates=config["maximum_candidates"],
        maximum_frame_age_ms=config["maximum_frame_age_ms"],
    )
    backend.load()
    backend.warmup()

    import cv2
    import torch

    rows = []
    latencies = []
    measured_iterations = int(config["smoke"]["measured_iterations_per_image"])
    for image_index, relative in enumerate(config["smoke"]["inputs"]):
        path = ROOT / relative
        image = cv2.imread(str(path))
        if image is None:
            raise RuntimeError(f"could not decode smoke input: {path}")
        observation = None
        image_latencies = []
        for iteration in range(measured_iterations + 1):
            captured_at_ns = time.time_ns()
            packet = FramePacket(
                frame_id=image_index * 100 + iteration,
                captured_at_ns=captured_at_ns,
                image_bgr=image,
                source="assignment_example_smoke",
                width=int(image.shape[1]),
                height=int(image.shape[0]),
            )
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            started = time.perf_counter_ns()
            observation = backend.infer(packet)
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            latency_ms = (time.perf_counter_ns() - started) / 1_000_000
            if iteration > 0:
                image_latencies.append(latency_ms)
                latencies.append(latency_ms)
        assert observation is not None
        rows.append(
            {
                "path": relative,
                "valid": observation.valid,
                "reason": observation.reason,
                "candidate_count": len(observation.boxes),
                "top_confidence": observation.boxes[0].confidence
                if observation.boxes
                else None,
                "mean_latency_ms": statistics.fmean(image_latencies),
                "p95_latency_ms": sorted(image_latencies)[
                    max(0, int(math.ceil(0.95 * len(image_latencies))) - 1)
                ],
            }
        )

    import ultralytics

    detected = sum(row["candidate_count"] > 0 for row in rows)
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "status": "SMOKE_COMPLETE_NOT_RELEASE_ADMITTED",
        "model_id": config["model_id"],
        "task": config["task"],
        "enabled_by_default": config["enabled_by_default"],
        "release_admitted": config["release_admitted"],
        "checkpoint": {
            "path": config["checkpoint"],
            "bytes": checkpoint.stat().st_size,
            "sha256": sha256(checkpoint),
        },
        "checksums": {
            "config": sha256(args.config),
            "localization_module": sha256(ROOT / "src" / "deskmate_baseline" / "localization.py"),
            "smoke_script": sha256(Path(__file__).resolve()),
        },
        "runtime": {
            "ultralytics": ultralytics.__version__,
            "torch": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "unavailable",
            "cat_class_id": backend.cat_class_id,
            "imgsz": config["imgsz"],
        },
        "smoke": {
            "role": config["smoke"]["role"],
            "training_allowed": config["smoke"]["training_allowed"],
            "images": len(rows),
            "images_with_cat_proposal": detected,
            "measured_iterations_per_image": measured_iterations,
            "measured_predictions": len(latencies),
            "mean_latency_ms": statistics.fmean(latencies),
            "p95_latency_ms": sorted(latencies)[max(0, int(math.ceil(0.95 * len(latencies))) - 1)]
            if latencies
            else None,
            "results": rows,
        },
        "limitations": [
            "assignment examples are smoke inputs, not training or accuracy evidence",
            "no real robot JPG or recorded robot video was available",
            "single images cannot validate temporal box stability",
            "centre-ROI classifier remains the release path",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    backend.close()
    return 0 if all(row["valid"] for row in rows) else 3


if __name__ == "__main__":
    raise SystemExit(main())
