from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs/baseline_inference_target5_robot.toml"
FROZEN_CONFIG = ROOT / "models/frozen/baseline-bd06-m09.toml"
FROZEN_RECORD = ROOT / "models/frozen/baseline-bd06-m09.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_default_runtime_resolves_to_frozen_bd06_and_m9() -> None:
    default = tomllib.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    frozen = tomllib.loads(FROZEN_CONFIG.read_text(encoding="utf-8"))
    record = json.loads(FROZEN_RECORD.read_text(encoding="utf-8"))

    for role in ("detector", "classifier"):
        assert default[role]["model_id"] == frozen[role]["model_id"]
        assert default[role]["checkpoint"] == frozen[role]["checkpoint"]
        assert default[role]["expected_sha256"] == frozen[role]["expected_sha256"]
        assert default[role]["download_url"] == frozen[role]["download_url"]
        checkpoint = ROOT / default[role]["checkpoint"]
        assert checkpoint.is_file()
        assert sha256(checkpoint) == default[role]["expected_sha256"]
        assert record["models"][role]["sha256"] == default[role]["expected_sha256"]

    assert default["routing"] == frozen["routing"]
    assert default["fallback"]["config"] == "models/frozen/baseline-bd05-m09.toml"


def test_manifest_marks_bd06_and_m9_as_default_release_models() -> None:
    manifest = yaml.safe_load((ROOT / "models/manifest.yaml").read_text(encoding="utf-8"))
    by_id = {model["id"]: model for model in manifest["models"]}
    for model_id in (
        "B-D06-FIVE-BREED-SCREENPRINT-FROM-PRETRAINED",
        "B-M09-TARGET5-MANUAL-CURATED-AUG-FROM-PRETRAINED",
    ):
        assert by_id[model_id]["state"] == "release"
        assert by_id[model_id]["enabled_priority"] == "P0_default"
