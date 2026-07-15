"""Five-breed classifier adapter; rejection remains outside the breed head."""

from __future__ import annotations

import math
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from ..domain.contracts import (
    INTERNAL_LABELS,
    REPORTABLE_LABELS,
    ClassificationObservation,
    FramePacket,
)
from .inference import (
    ClassMappingError,
    _normalize_native_name,
    _probability_values,
    extract_center_roi,
)


def target_index_mapping(
    native_names: Mapping[int, str] | Sequence[str],
) -> tuple[int, ...]:
    """Return canonical target indices for an exact five-breed checkpoint."""
    if isinstance(native_names, (str, bytes)):
        raise ClassMappingError("checkpoint class names must be a mapping or sequence")
    if isinstance(native_names, Mapping):
        names = {int(index): str(name) for index, name in native_names.items()}
    else:
        names = {index: str(name) for index, name in enumerate(native_names)}
    expected_indices = set(range(len(REPORTABLE_LABELS)))
    if set(names) != expected_indices:
        raise ClassMappingError(
            f"checkpoint must expose exactly five contiguous target classes; got {len(names)}"
        )
    normalized = [_normalize_native_name(names[index]) for index in range(len(names))]
    if len(set(normalized)) != len(normalized):
        raise ClassMappingError("checkpoint class names are not unique")
    if set(normalized) != set(REPORTABLE_LABELS):
        missing = sorted(set(REPORTABLE_LABELS) - set(normalized))
        extra = sorted(set(normalized) - set(REPORTABLE_LABELS))
        raise ClassMappingError(f"target mapping mismatch; missing={missing} extra={extra}")
    return tuple(normalized.index(label) for label in REPORTABLE_LABELS)


def normalize_target_probabilities(
    probabilities: Sequence[float], temperature: float = 1.0
) -> tuple[float, ...]:
    """Temperature-scale five targets and append a zero rejection probability."""
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    if len(probabilities) != len(REPORTABLE_LABELS):
        raise ValueError("native probability count is not five")
    if any(not math.isfinite(value) or value < 0 for value in probabilities):
        raise ValueError("native probabilities must be finite and non-negative")
    total = sum(probabilities)
    if total <= 0:
        raise ValueError("native probabilities sum to zero")
    normalized = [max(value / total, 1e-12) for value in probabilities]
    logits = [math.log(value) / temperature for value in normalized]
    offset = max(logits)
    exponentials = [math.exp(value - offset) for value in logits]
    denominator = sum(exponentials)
    targets = tuple(value / denominator for value in exponentials)
    return (*targets, 0.0)


def fuse_target_probabilities(
    probability_sets: Sequence[Sequence[float]],
    weights: Sequence[float] | None = None,
) -> tuple[float, ...]:
    """Average target-only observations while preserving the six-slot contract."""
    if not probability_sets:
        raise ValueError("at least one probability set is required")
    actual_weights = tuple(weights or (1.0,) * len(probability_sets))
    if len(actual_weights) != len(probability_sets):
        raise ValueError("weights must match probability sets")
    if any(not math.isfinite(weight) or weight <= 0 for weight in actual_weights):
        raise ValueError("fusion weights must be finite and positive")
    targets = [0.0] * len(REPORTABLE_LABELS)
    for probabilities, weight in zip(probability_sets, actual_weights):
        if len(probabilities) != len(INTERNAL_LABELS):
            raise ValueError("probabilities must follow the six-slot contract")
        for index in range(len(REPORTABLE_LABELS)):
            targets[index] += float(probabilities[index]) * weight
    total = sum(targets)
    if total <= 0:
        raise ValueError("fused target probability sum is zero")
    return (*(value / total for value in targets), 0.0)


class UltralyticsTargetClassificationBackend:
    """Run an exact five-breed model and pad its output for existing consumers."""

    def __init__(
        self,
        *,
        checkpoint: Path,
        model_id: str = "B-M02-TARGET5",
        device: int | str = 0,
        imgsz: int = 224,
        temperature: float = 1.0,
        maximum_frame_age_ms: float = 500.0,
        roi_scales: Mapping[str, float] | None = None,
        model_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.checkpoint = checkpoint
        self.model_id = model_id
        self.device = device
        self.imgsz = imgsz
        self.temperature = temperature
        self.maximum_frame_age_ns = int(maximum_frame_age_ms * 1_000_000)
        self.roi_scales = dict(roi_scales or {"wide": 1.0, "medium": 0.8, "tight": 0.6})
        self._model_factory = model_factory
        self._model: Any | None = None
        self._canonical_to_native: tuple[int, ...] | None = None
        self._health = "not_loaded"

    def load(self) -> None:
        if not self.checkpoint.is_file():
            self._health = "missing_checkpoint"
            raise FileNotFoundError(self.checkpoint)
        try:
            factory = self._model_factory
            if factory is None:
                from ultralytics import YOLO

                factory = YOLO
            model = factory(str(self.checkpoint), task="classify")
            mapping = target_index_mapping(model.names)
        except Exception as exc:
            self._model = None
            self._canonical_to_native = None
            self._health = f"load_error:{type(exc).__name__}:{exc}"
            raise
        self._model = model
        self._canonical_to_native = mapping
        self._health = "ready"

    def warmup(self) -> None:
        if self._model is None:
            raise RuntimeError("backend is not loaded")
        import numpy as np

        self._model.predict(
            source=np.zeros((self.imgsz, self.imgsz, 3), dtype=np.uint8),
            imgsz=self.imgsz,
            device=self.device,
            verbose=False,
        )

    def infer(self, frame: FramePacket, roi_scale: str) -> ClassificationObservation:
        now_ns = max(time.time_ns(), frame.captured_at_ns)
        if self._model is None or self._canonical_to_native is None:
            return ClassificationObservation.invalid(
                frame=frame,
                model_id=self.model_id,
                roi_scale=roi_scale,
                inferred_at_ns=now_ns,
                reason=f"backend_not_ready:{self._health}",
            )
        if now_ns - frame.captured_at_ns > self.maximum_frame_age_ns:
            return ClassificationObservation.invalid(
                frame=frame,
                model_id=self.model_id,
                roi_scale=roi_scale,
                inferred_at_ns=now_ns,
                reason="stale_frame",
            )
        try:
            scale = self.roi_scales[roi_scale]
            shape = getattr(frame.image_bgr, "shape", ())
            if len(shape) != 3 or (int(shape[1]), int(shape[0])) != (
                frame.width,
                frame.height,
            ):
                raise ValueError("frame metadata does not match image dimensions")
            roi = extract_center_roi(frame.image_bgr, scale)
            results = self._model.predict(
                source=roi, imgsz=self.imgsz, device=self.device, verbose=False
            )
            if len(results) != 1 or getattr(results[0], "probs", None) is None:
                raise ValueError("classification result is missing Results.probs")
            native = _probability_values(results[0].probs)
            canonical = [native[index] for index in self._canonical_to_native]
            probabilities = normalize_target_probabilities(canonical, self.temperature)
            ranked = sorted(
                zip(INTERNAL_LABELS, probabilities), key=lambda item: item[1], reverse=True
            )
            self._health = "ready"
            return ClassificationObservation(
                task="cat_breed",
                label=ranked[0][0],
                probabilities=probabilities,
                calibrated_confidence=ranked[0][1],
                margin=ranked[0][1] - ranked[1][1],
                topk=tuple(ranked[:3]),
                model_id=self.model_id,
                roi_scale=roi_scale,
                frame_id=frame.frame_id,
                captured_at_ns=frame.captured_at_ns,
                inferred_at_ns=max(time.time_ns(), frame.captured_at_ns),
                valid=True,
            )
        except Exception as exc:
            self._health = f"inference_error:{type(exc).__name__}:{exc}"
            return ClassificationObservation.invalid(
                frame=frame,
                model_id=self.model_id,
                roi_scale=roi_scale,
                inferred_at_ns=max(time.time_ns(), frame.captured_at_ns),
                reason=self._health,
            )

    def health(self) -> str:
        return self._health

    def close(self) -> None:
        self._model = None
        self._canonical_to_native = None
        self._health = "closed"
