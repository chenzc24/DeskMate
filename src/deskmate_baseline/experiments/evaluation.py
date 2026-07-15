"""Framework-neutral metrics and leak-resistant scalar calibration."""

from __future__ import annotations

import csv
import hashlib
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from ..domain.contracts import INTERNAL_LABELS, REPORTABLE_LABELS


PROBABILITY_FIELDS = tuple(f"p_{label}" for label in INTERNAL_LABELS)
PREDICTION_FIELDS = (
    "image_id",
    "split",
    "true_label",
    *PROBABILITY_FIELDS,
    "model_id",
    "dataset_sha256",
    "checkpoint_sha256",
    "source_group_id",
)
ALLOWED_EVALUATION_SPLITS = {
    "val_select",
    "val_cal",
    "robot_calibration",
    "robot_final",
}


@dataclass(frozen=True, slots=True)
class PredictionRow:
    image_id: str
    split: str
    true_label: str
    probabilities: tuple[float, ...]
    model_id: str
    dataset_sha256: str
    checkpoint_sha256: str
    source_group_id: str


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value.casefold())


def read_prediction_manifest(path: Path) -> list[PredictionRow]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != PREDICTION_FIELDS:
            raise ValueError("prediction manifest headers or canonical probability order are invalid")
        raw_rows = list(reader)
    rows: list[PredictionRow] = []
    seen_ids: set[str] = set()
    provenance: set[tuple[str, str, str]] = set()
    for number, raw in enumerate(raw_rows, start=2):
        image_id = (raw["image_id"] or "").strip()
        if not image_id or image_id in seen_ids:
            raise ValueError(f"missing or duplicate image_id on row {number}")
        seen_ids.add(image_id)
        split = (raw["split"] or "").strip()
        label = (raw["true_label"] or "").strip()
        if split not in ALLOWED_EVALUATION_SPLITS:
            raise ValueError(f"invalid evaluation split on row {number}")
        if label not in INTERNAL_LABELS:
            raise ValueError(f"invalid true label on row {number}")
        try:
            probabilities = tuple(float(raw[field]) for field in PROBABILITY_FIELDS)
        except ValueError as exc:
            raise ValueError(f"invalid probability on row {number}") from exc
        if any(not math.isfinite(value) or value < 0 or value > 1 for value in probabilities):
            raise ValueError(f"probability outside [0, 1] on row {number}")
        if abs(sum(probabilities) - 1.0) > 1e-6:
            raise ValueError(f"probabilities do not sum to one on row {number}")
        model_id = (raw["model_id"] or "").strip()
        dataset_hash = (raw["dataset_sha256"] or "").strip().casefold()
        checkpoint_hash = (raw["checkpoint_sha256"] or "").strip().casefold()
        source_group = (raw["source_group_id"] or "").strip()
        if not model_id or not source_group or not _is_sha256(dataset_hash) or not _is_sha256(checkpoint_hash):
            raise ValueError(f"missing or invalid provenance on row {number}")
        provenance.add((model_id, dataset_hash, checkpoint_hash))
        rows.append(PredictionRow(
            image_id=image_id,
            split=split,
            true_label=label,
            probabilities=probabilities,
            model_id=model_id,
            dataset_sha256=dataset_hash,
            checkpoint_sha256=checkpoint_hash,
            source_group_id=source_group,
        ))
    if not rows:
        raise ValueError("prediction manifest is empty")
    if len(provenance) != 1:
        raise ValueError("prediction manifest mixes model, dataset, or checkpoint provenance")
    return rows


def temperature_scale(
    probabilities: Sequence[float], temperature: float
) -> tuple[float, ...]:
    if temperature <= 0 or not math.isfinite(temperature):
        raise ValueError("temperature must be finite and positive")
    if len(probabilities) != len(INTERNAL_LABELS):
        raise ValueError("probability vector must follow canonical six-class order")
    logits = [math.log(max(float(value), 1e-12)) / temperature for value in probabilities]
    offset = max(logits)
    values = [math.exp(value - offset) for value in logits]
    total = sum(values)
    return tuple(value / total for value in values)


def _prediction(probabilities: Sequence[float]) -> str:
    return INTERNAL_LABELS[max(range(len(probabilities)), key=probabilities.__getitem__)]


def negative_log_likelihood(rows: Sequence[PredictionRow], temperature: float = 1.0) -> float:
    losses = []
    for row in rows:
        calibrated = temperature_scale(row.probabilities, temperature)
        true_index = INTERNAL_LABELS.index(row.true_label)
        losses.append(-math.log(max(calibrated[true_index], 1e-12)))
    return sum(losses) / len(losses)


def expected_calibration_error(
    rows: Sequence[PredictionRow], *, temperature: float = 1.0, bins: int = 15
) -> float:
    if bins <= 0:
        raise ValueError("ECE bins must be positive")
    buckets: list[list[tuple[float, bool]]] = [[] for _ in range(bins)]
    for row in rows:
        calibrated = temperature_scale(row.probabilities, temperature)
        confidence = max(calibrated)
        index = min(bins - 1, int(confidence * bins))
        buckets[index].append((confidence, _prediction(calibrated) == row.true_label))
    total = len(rows)
    return sum(
        len(bucket) / total
        * abs(sum(confidence for confidence, _ in bucket) / len(bucket) - sum(correct for _, correct in bucket) / len(bucket))
        for bucket in buckets
        if bucket
    )


def fit_temperature(
    rows: Sequence[PredictionRow], *, minimum: float, maximum: float, steps: int
) -> dict[str, float]:
    if not rows or {row.split for row in rows} != {"val_cal"}:
        raise ValueError("temperature fitting accepts val_cal rows only")
    if steps < 2 or not 0 < minimum < maximum:
        raise ValueError("invalid temperature search range")
    candidates = [minimum + index * (maximum - minimum) / (steps - 1) for index in range(steps)]
    scored = [(negative_log_likelihood(rows, value), value) for value in candidates]
    after_nll, temperature = min(scored, key=lambda item: (item[0], item[1]))
    return {
        "temperature": temperature,
        "nll_before": negative_log_likelihood(rows),
        "nll_after": after_nll,
    }


def evaluate_predictions(
    rows: Sequence[PredictionRow], *, temperature: float = 1.0, ece_bins: int = 15
) -> dict[str, Any]:
    if not rows:
        raise ValueError("evaluation requires rows")
    splits = {row.split for row in rows}
    if len(splits) != 1:
        raise ValueError("one evaluation report cannot mix split roles")
    confusion = [[0 for _ in INTERNAL_LABELS] for _ in INTERNAL_LABELS]
    predictions: list[str] = []
    for row in rows:
        predicted = _prediction(temperature_scale(row.probabilities, temperature))
        predictions.append(predicted)
        confusion[INTERNAL_LABELS.index(row.true_label)][INTERNAL_LABELS.index(predicted)] += 1
    per_class_recall = {}
    for index, label in enumerate(INTERNAL_LABELS):
        total = sum(confusion[index])
        per_class_recall[label] = confusion[index][index] / total if total else None
    target_indices = [index for index, row in enumerate(rows) if row.true_label in REPORTABLE_LABELS]
    target_correct = sum(predictions[index] == rows[index].true_label for index in target_indices)
    f1_values = []
    for label in REPORTABLE_LABELS:
        tp = sum(row.true_label == label and predictions[index] == label for index, row in enumerate(rows) if row.true_label in REPORTABLE_LABELS)
        fp = sum(row.true_label != label and predictions[index] == label for index, row in enumerate(rows) if row.true_label in REPORTABLE_LABELS)
        fn = sum(row.true_label == label and predictions[index] != label for index, row in enumerate(rows) if row.true_label in REPORTABLE_LABELS)
        f1_values.append(2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0)
    negative_indices = [index for index, row in enumerate(rows) if row.true_label == "not_target"]
    return {
        "schema_version": 1,
        "split": next(iter(splits)),
        "rows": len(rows),
        "temperature": temperature,
        "class_order": list(INTERNAL_LABELS),
        "confusion_matrix": confusion,
        "six_class_accuracy": sum(predictions[index] == row.true_label for index, row in enumerate(rows)) / len(rows),
        "target_rows": len(target_indices),
        "target_accuracy": target_correct / len(target_indices) if target_indices else None,
        "target_macro_f1": sum(f1_values) / len(f1_values) if target_indices else None,
        "per_class_recall": per_class_recall,
        "negative_rows": len(negative_indices),
        "negative_rejection_rate": sum(predictions[index] == "not_target" for index in negative_indices) / len(negative_indices) if negative_indices else None,
        "nll": negative_log_likelihood(rows, temperature),
        "ece": expected_calibration_error(rows, temperature=temperature, bins=ece_bins),
        "model_id": rows[0].model_id,
        "dataset_sha256": rows[0].dataset_sha256,
        "checkpoint_sha256": rows[0].checkpoint_sha256,
    }


def prediction_manifest_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
