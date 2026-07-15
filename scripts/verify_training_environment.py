"""Verify the pinned CUDA stack and B-M01 base asset without training."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest", type=Path, default=ROOT / "models" / "manifest.yaml"
    )
    parser.add_argument("--image", type=Path)
    args = parser.parse_args()

    import torch
    import torchvision
    import ultralytics

    document = yaml.safe_load(args.manifest.read_text(encoding="utf-8"))
    entry = next(model for model in document["models"] if model["id"] == "B-M01-BASE")
    weight = ROOT / entry["file"]
    checks = {
        "python_3_12": sys.version_info[:2] == (3, 12),
        "torch": torch.__version__ == entry["environment"]["torch"],
        "torchvision": torchvision.__version__ == entry["environment"]["torchvision"],
        "ultralytics": ultralytics.__version__ == entry["environment"]["ultralytics"],
        "cuda_available": torch.cuda.is_available(),
        "weight_exists": weight.is_file(),
        "weight_sha256": weight.is_file() and sha256(weight) == entry["sha256"],
        "weight_bytes": weight.is_file() and weight.stat().st_size == entry["bytes"],
    }
    report = {
        "schema_version": 1,
        "ready": all(checks.values()),
        "checks": checks,
        "environment": {
            "python": sys.version.split()[0],
            "torch": torch.__version__,
            "torchvision": torchvision.__version__,
            "ultralytics": ultralytics.__version__,
            "cuda_runtime": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        },
        "weight": {"path": entry["file"], "sha256": sha256(weight) if weight.is_file() else None},
    }
    if args.image:
        from ultralytics import YOLO

        result = YOLO(str(weight), task="classify").predict(
            str(args.image), imgsz=224, device=0, verbose=False
        )[0]
        report["smoke"] = {
            "task": "classify",
            "probs_present": result.probs is not None,
            "boxes_present": result.boxes is not None,
            "top1": result.names[int(result.probs.top1)],
            "confidence": float(result.probs.top1conf),
            "evidence_role": "framework_smoke_only",
        }
        report["ready"] = report["ready"] and result.probs is not None and result.boxes is None
    print(json.dumps(report, indent=2))
    return 0 if report["ready"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
