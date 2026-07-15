"""Prove that the ImageNet base weight cannot masquerade as Cat Census output."""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from deskmate_baseline.perception.inference import (  # noqa: E402
    ClassMappingError,
    UltralyticsClassificationBackend,
)


def main() -> int:
    config = tomllib.loads((ROOT / "configs" / "baseline_inference.toml").read_text(encoding="utf-8"))
    backend = UltralyticsClassificationBackend(
        checkpoint=ROOT / config["checkpoint"],
        model_id=config["model_id"],
        device=config["device"],
        imgsz=config["imgsz"],
        temperature=config["temperature"],
        maximum_frame_age_ms=config["maximum_frame_age_ms"],
        roi_scales=config["roi_scales"],
    )
    try:
        backend.load()
    except ClassMappingError as exc:
        print(json.dumps({
            "passed": True,
            "base_weight_rejected": True,
            "reason": str(exc),
            "health": backend.health(),
            "species_output_emitted": False,
        }, indent=2))
        return 0
    print(json.dumps({
        "passed": False,
        "base_weight_rejected": False,
        "health": backend.health(),
    }, indent=2))
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
