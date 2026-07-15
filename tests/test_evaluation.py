from __future__ import annotations

import csv
from pathlib import Path

import pytest

from deskmate_baseline.contracts import INTERNAL_LABELS
from deskmate_baseline.evaluation import (
    PREDICTION_FIELDS,
    PredictionRow,
    evaluate_predictions,
    fit_temperature,
    read_prediction_manifest,
    temperature_scale,
)


HASH_A = "a" * 64
HASH_B = "b" * 64


def row(image_id: str, label: str, probabilities, split: str = "val_cal") -> PredictionRow:
    return PredictionRow(image_id, split, label, tuple(probabilities), "B-M01", HASH_A, HASH_B, image_id)


def test_metrics_match_hand_computed_fixture() -> None:
    rows = [
        row("r1", "ragdoll", (0.8, 0.1, 0.025, 0.025, 0.025, 0.025)),
        row("r2", "ragdoll", (0.1, 0.8, 0.025, 0.025, 0.025, 0.025)),
        row("s1", "singapura", (0.1, 0.8, 0.025, 0.025, 0.025, 0.025)),
        row("n1", "not_target", (0.02, 0.02, 0.02, 0.02, 0.02, 0.9)),
    ]
    report = evaluate_predictions(rows, ece_bins=5)
    assert report["six_class_accuracy"] == pytest.approx(0.75)
    assert report["target_accuracy"] == pytest.approx(2 / 3)
    assert report["per_class_recall"]["ragdoll"] == pytest.approx(0.5)
    assert report["per_class_recall"]["singapura"] == pytest.approx(1.0)
    assert report["negative_rejection_rate"] == pytest.approx(1.0)
    assert sum(sum(values) for values in report["confusion_matrix"]) == 4


def test_temperature_fit_uses_only_val_cal_and_improves_overconfident_errors() -> None:
    rows = [
        row("a", "ragdoll", (0.01, 0.95, 0.01, 0.01, 0.01, 0.01)),
        row("b", "singapura", (0.95, 0.01, 0.01, 0.01, 0.01, 0.01)),
    ]
    result = fit_temperature(rows, minimum=0.5, maximum=5.0, steps=451)
    assert result["temperature"] > 1.0
    assert result["nll_after"] < result["nll_before"]
    assert sum(temperature_scale(rows[0].probabilities, result["temperature"])) == pytest.approx(1.0)
    mixed = [rows[0], row("c", "ragdoll", rows[0].probabilities, split="val_select")]
    with pytest.raises(ValueError, match="val_cal rows only"):
        fit_temperature(mixed, minimum=0.5, maximum=5.0, steps=20)


def test_evaluation_refuses_mixed_split_roles() -> None:
    rows = [
        row("a", "ragdoll", (0.8, 0.1, 0.025, 0.025, 0.025, 0.025)),
        row("b", "ragdoll", (0.8, 0.1, 0.025, 0.025, 0.025, 0.025), split="val_select"),
    ]
    with pytest.raises(ValueError, match="mix split roles"):
        evaluate_predictions(rows)


def test_prediction_manifest_validates_order_duplicates_and_provenance(tmp_path: Path) -> None:
    path = tmp_path / "predictions.csv"
    raw = {
        "image_id": "one", "split": "val_select", "true_label": "ragdoll",
        **{f"p_{label}": "0" for label in INTERNAL_LABELS},
        "model_id": "B-M01", "dataset_sha256": HASH_A,
        "checkpoint_sha256": HASH_B, "source_group_id": "group-one",
    }
    raw["p_ragdoll"] = "1"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PREDICTION_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerow(raw)
    assert read_prediction_manifest(path)[0].true_label == "ragdoll"
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PREDICTION_FIELDS, lineterminator="\n")
        writer.writerow(raw)
    with pytest.raises(ValueError, match="duplicate image_id"):
        read_prediction_manifest(path)
