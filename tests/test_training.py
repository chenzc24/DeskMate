from pathlib import Path

import pytest

from deskmate_baseline.contracts import INTERNAL_LABELS
from deskmate_baseline.training import build_training_plan, load_training_config


def test_training_config_and_dry_run_plan() -> None:
    path = Path("configs/baseline_training.toml")
    config = load_training_config(path)
    plan = build_training_plan(config_path=path)
    assert tuple(config["dataset"]["labels"]) == INTERNAL_LABELS
    assert plan["task"] == "classify"
    assert plan["weights"].endswith("yolo26s-cls.pt")
    assert plan["kwargs"]["imgsz"] == 224
    assert plan["execution_authorized"] is False


def test_training_plan_refuses_unfrozen_seed() -> None:
    with pytest.raises(ValueError, match="frozen comparison seeds"):
        build_training_plan(config_path=Path("configs/baseline_training.toml"), seed=1)
