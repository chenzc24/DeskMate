"""Ultralytics classification adapter with strict six-class containment."""

from __future__ import annotations

import math
import re
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from ..domain.contracts import INTERNAL_LABELS, ClassificationObservation, FramePacket


INDEXED_NAME = re.compile(r"^(\d+)[_-](.+)$")


class ClassMappingError(ValueError):
    """Raised when a checkpoint cannot produce the canonical six outputs."""


def _normalize_native_name(value: str) -> str:
    normalized = value.strip().casefold().replace(" ", "_")
    match = INDEXED_NAME.fullmatch(normalized)
    return match.group(2) if match else normalized


def canonical_index_mapping(
    native_names: Mapping[int, str] | Sequence[str],
) -> tuple[int, ...]:
    """Validate a one-to-one native name mapping and return canonical indices."""
    if isinstance(native_names, (str, bytes)):
        raise ClassMappingError("checkpoint class names must be a mapping or sequence")
    if isinstance(native_names, Mapping):
        names = {int(index): str(name) for index, name in native_names.items()}
    else:
        names = {index: str(name) for index, name in enumerate(native_names)}
    expected_indices = set(range(len(INTERNAL_LABELS)))
    if set(names) != expected_indices:
        raise ClassMappingError(
            f"checkpoint must expose exactly six contiguous classes; got {len(names)}"
        )
    normalized = [_normalize_native_name(names[index]) for index in range(len(names))]
    if len(set(normalized)) != len(normalized):
        raise ClassMappingError("checkpoint class names are not unique")
    if set(normalized) != set(INTERNAL_LABELS):
        missing = sorted(set(INTERNAL_LABELS) - set(normalized))
        extra = sorted(set(normalized) - set(INTERNAL_LABELS))
        raise ClassMappingError(f"class mapping mismatch; missing={missing} extra={extra}")
    return tuple(normalized.index(label) for label in INTERNAL_LABELS)


def extract_center_roi(image_bgr: Any, scale: float) -> Any:
    """Return a copied, centred, bounded HWC ROI without resizing it."""
    if not 0.0 < scale <= 1.0:
        raise ValueError("ROI scale must be within (0, 1]")
    shape = getattr(image_bgr, "shape", None)
    if shape is None or len(shape) != 3 or shape[2] != 3:
        raise ValueError("frame image must be an HxWx3 array")
    height, width = int(shape[0]), int(shape[1])
    if height <= 0 or width <= 0:
        raise ValueError("frame image must be non-empty")
    roi_height = max(1, min(height, int(round(height * scale))))
    roi_width = max(1, min(width, int(round(width * scale))))
    top = (height - roi_height) // 2
    left = (width - roi_width) // 2
    return image_bgr[top : top + roi_height, left : left + roi_width].copy()


def _probability_values(native_probs: Any) -> list[float]:
    values = getattr(native_probs, "data", native_probs)
    for method in ("detach", "float", "cpu"):
        function = getattr(values, method, None)
        if callable(function):
            values = function()
    if hasattr(values, "tolist"):
        values = values.tolist()
    return [float(value) for value in values]


def _temperature_scale(probabilities: Sequence[float], temperature: float) -> tuple[float, ...]:
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    if len(probabilities) != len(INTERNAL_LABELS):
        raise ValueError("native probability count is not six")
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
    return tuple(value / denominator for value in exponentials)


class UltralyticsClassificationBackend:
    """Contain all framework objects behind the ModelRunner contract."""

    def __init__(
        self,
        *,
        checkpoint: Path,
        model_id: str = "B-M01",
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
            mapping = canonical_index_mapping(model.names)
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
            probabilities = _temperature_scale(canonical, self.temperature)
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
