"""Framework-contained cat localizer and centre-ROI-safe crop routing."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .contracts import FramePacket
from .inference import extract_center_roi


class LocalizerMappingError(ValueError):
    """Raised when the detector cannot resolve exactly one native cat class."""


def resolve_native_class_id(
    native_names: Mapping[int, str] | Sequence[str], target: str = "cat"
) -> int:
    if isinstance(native_names, (str, bytes)):
        raise LocalizerMappingError("detector names must be a mapping or sequence")
    items = native_names.items() if isinstance(native_names, Mapping) else enumerate(native_names)
    matches = [int(index) for index, name in items if str(name).strip().casefold() == target]
    if len(matches) != 1:
        raise LocalizerMappingError(
            f"detector must expose exactly one {target!r} class; found {len(matches)}"
        )
    return matches[0]


@dataclass(frozen=True, slots=True)
class LocalizerBox:
    """One normalized cat-content proposal with no breed semantics."""

    xyxy: tuple[float, float, float, float]
    confidence: float
    native_class_id: int

    def __post_init__(self) -> None:
        x1, y1, x2, y2 = self.xyxy
        if not all(math.isfinite(value) and 0.0 <= value <= 1.0 for value in self.xyxy):
            raise ValueError("normalized box coordinates must be finite within [0, 1]")
        if x2 <= x1 or y2 <= y1:
            raise ValueError("box must have positive area")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within [0, 1]")
        if self.native_class_id < 0:
            raise ValueError("native_class_id must be non-negative")

    @property
    def area_ratio(self) -> float:
        x1, y1, x2, y2 = self.xyxy
        return (x2 - x1) * (y2 - y1)


@dataclass(frozen=True, slots=True)
class LocalizerObservation:
    """Typed detector output; it cannot represent or print a cat breed."""

    task: str
    boxes: tuple[LocalizerBox, ...]
    model_id: str
    frame_id: int
    captured_at_ns: int
    inferred_at_ns: int
    valid: bool
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.task != "cat_localization":
            raise ValueError("localizer task must be cat_localization")
        if self.inferred_at_ns < self.captured_at_ns:
            raise ValueError("inference cannot precede capture")
        if self.valid and self.reason is not None:
            raise ValueError("valid observation cannot have an invalid reason")
        if not self.valid and not self.reason:
            raise ValueError("invalid observation must explain its reason")

    @classmethod
    def invalid(
        cls, *, frame: FramePacket, model_id: str, inferred_at_ns: int, reason: str
    ) -> "LocalizerObservation":
        return cls(
            task="cat_localization",
            boxes=(),
            model_id=model_id,
            frame_id=frame.frame_id,
            captured_at_ns=frame.captured_at_ns,
            inferred_at_ns=inferred_at_ns,
            valid=False,
            reason=reason,
        )


@dataclass(frozen=True, slots=True)
class RoutedROI:
    """A copied classification ROI selected from a stable box or centre fallback."""

    image_bgr: Any
    pixel_xyxy: tuple[int, int, int, int]
    mode: str
    frame_id: int
    source_confidence: float | None

    def __post_init__(self) -> None:
        if self.mode not in {"detector_crop", "centre_fallback"}:
            raise ValueError("unknown route mode")


def _native_values(value: Any) -> list[Any]:
    for method in ("detach", "cpu"):
        function = getattr(value, method, None)
        if callable(function):
            value = function()
    if hasattr(value, "tolist"):
        value = value.tolist()
    return list(value)


def _center_bounds(width: int, height: int, scale: float) -> tuple[int, int, int, int]:
    roi_height = max(1, min(height, int(round(height * scale))))
    roi_width = max(1, min(width, int(round(width * scale))))
    top = (height - roi_height) // 2
    left = (width - roi_width) // 2
    return left, top, left + roi_width, top + roi_height


def route_classification_roi(
    frame: FramePacket,
    observation: LocalizerObservation | None,
    *,
    box_is_stable: bool,
    padding_ratio: float = 0.15,
    fallback_center_scale: float = 0.8,
) -> RoutedROI:
    """Route only a same-frame stable proposal; otherwise copy the centre ROI."""
    if padding_ratio < 0:
        raise ValueError("padding_ratio must be non-negative")
    shape = getattr(frame.image_bgr, "shape", ())
    if len(shape) != 3 or int(shape[2]) != 3 or (int(shape[1]), int(shape[0])) != (
        frame.width,
        frame.height,
    ):
        raise ValueError("frame metadata does not match image dimensions")

    usable = (
        observation is not None
        and observation.valid
        and observation.frame_id == frame.frame_id
        and observation.captured_at_ns == frame.captured_at_ns
        and bool(observation.boxes)
        and box_is_stable
    )
    if usable:
        box = observation.boxes[0]
        x1, y1, x2, y2 = box.xyxy
        pad_x = (x2 - x1) * padding_ratio
        pad_y = (y2 - y1) * padding_ratio
        left = max(0, int(math.floor((x1 - pad_x) * frame.width)))
        top = max(0, int(math.floor((y1 - pad_y) * frame.height)))
        right = min(frame.width, int(math.ceil((x2 + pad_x) * frame.width)))
        bottom = min(frame.height, int(math.ceil((y2 + pad_y) * frame.height)))
        if right > left and bottom > top:
            return RoutedROI(
                image_bgr=frame.image_bgr[top:bottom, left:right].copy(),
                pixel_xyxy=(left, top, right, bottom),
                mode="detector_crop",
                frame_id=frame.frame_id,
                source_confidence=box.confidence,
            )

    left, top, right, bottom = _center_bounds(
        frame.width, frame.height, fallback_center_scale
    )
    return RoutedROI(
        image_bgr=extract_center_roi(frame.image_bgr, fallback_center_scale),
        pixel_xyxy=(left, top, right, bottom),
        mode="centre_fallback",
        frame_id=frame.frame_id,
        source_confidence=None,
    )


class UltralyticsCatLocalizerBackend:
    """Contain Ultralytics detection results behind a typed observation."""

    def __init__(
        self,
        *,
        checkpoint: Path,
        model_id: str = "B-D01",
        device: int | str = 0,
        imgsz: int = 640,
        confidence_threshold: float = 0.25,
        minimum_box_area_ratio: float = 0.02,
        maximum_candidates: int = 5,
        maximum_frame_age_ms: float = 500.0,
        model_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.checkpoint = checkpoint
        self.model_id = model_id
        self.device = device
        self.imgsz = imgsz
        self.confidence_threshold = confidence_threshold
        self.minimum_box_area_ratio = minimum_box_area_ratio
        self.maximum_candidates = maximum_candidates
        self.maximum_frame_age_ns = int(maximum_frame_age_ms * 1_000_000)
        self._model_factory = model_factory
        self._model: Any | None = None
        self._cat_class_id: int | None = None
        self._health = "not_loaded"

    @property
    def cat_class_id(self) -> int | None:
        return self._cat_class_id

    def load(self) -> None:
        if not self.checkpoint.is_file():
            self._health = "missing_checkpoint"
            raise FileNotFoundError(self.checkpoint)
        try:
            factory = self._model_factory
            if factory is None:
                from ultralytics import YOLO

                factory = YOLO
            model = factory(str(self.checkpoint), task="detect")
            cat_class_id = resolve_native_class_id(model.names)
        except Exception as exc:
            self._model = None
            self._cat_class_id = None
            self._health = f"load_error:{type(exc).__name__}:{exc}"
            raise
        self._model = model
        self._cat_class_id = cat_class_id
        self._health = "ready"

    def warmup(self) -> None:
        if self._model is None or self._cat_class_id is None:
            raise RuntimeError("backend is not loaded")
        import numpy as np

        self._model.predict(
            source=np.zeros((self.imgsz, self.imgsz, 3), dtype=np.uint8),
            imgsz=self.imgsz,
            device=self.device,
            classes=[self._cat_class_id],
            max_det=self.maximum_candidates,
            verbose=False,
        )

    def infer(self, frame: FramePacket, _roi_scale: str = "full") -> LocalizerObservation:
        now_ns = max(time.time_ns(), frame.captured_at_ns)
        if self._model is None or self._cat_class_id is None:
            return LocalizerObservation.invalid(
                frame=frame,
                model_id=self.model_id,
                inferred_at_ns=now_ns,
                reason=f"backend_not_ready:{self._health}",
            )
        if now_ns - frame.captured_at_ns > self.maximum_frame_age_ns:
            return LocalizerObservation.invalid(
                frame=frame,
                model_id=self.model_id,
                inferred_at_ns=now_ns,
                reason="stale_frame",
            )
        try:
            shape = getattr(frame.image_bgr, "shape", ())
            if len(shape) != 3 or (int(shape[1]), int(shape[0])) != (
                frame.width,
                frame.height,
            ):
                raise ValueError("frame metadata does not match image dimensions")
            results = self._model.predict(
                source=frame.image_bgr,
                imgsz=self.imgsz,
                device=self.device,
                conf=self.confidence_threshold,
                classes=[self._cat_class_id],
                max_det=self.maximum_candidates,
                verbose=False,
            )
            if len(results) != 1 or getattr(results[0], "boxes", None) is None:
                raise ValueError("detection result is missing Results.boxes")
            native = results[0].boxes
            xyxyn = _native_values(native.xyxyn)
            confidences = _native_values(native.conf)
            classes = _native_values(native.cls)
            if not (len(xyxyn) == len(confidences) == len(classes)):
                raise ValueError("detection box arrays have inconsistent lengths")
            boxes: list[LocalizerBox] = []
            for coordinates, confidence, class_id in zip(xyxyn, confidences, classes):
                if int(class_id) != self._cat_class_id:
                    continue
                box = LocalizerBox(
                    xyxy=tuple(float(value) for value in coordinates),
                    confidence=float(confidence),
                    native_class_id=int(class_id),
                )
                if (
                    box.confidence >= self.confidence_threshold
                    and box.area_ratio >= self.minimum_box_area_ratio
                ):
                    boxes.append(box)
            boxes.sort(key=lambda box: (box.confidence, box.area_ratio), reverse=True)
            self._health = "ready"
            return LocalizerObservation(
                task="cat_localization",
                boxes=tuple(boxes[: self.maximum_candidates]),
                model_id=self.model_id,
                frame_id=frame.frame_id,
                captured_at_ns=frame.captured_at_ns,
                inferred_at_ns=max(time.time_ns(), frame.captured_at_ns),
                valid=True,
            )
        except Exception as exc:
            self._health = f"inference_error:{type(exc).__name__}:{exc}"
            return LocalizerObservation.invalid(
                frame=frame,
                model_id=self.model_id,
                inferred_at_ns=max(time.time_ns(), frame.captured_at_ns),
                reason=self._health,
            )

    def health(self) -> str:
        return self._health

    def close(self) -> None:
        self._model = None
        self._cat_class_id = None
        self._health = "closed"
