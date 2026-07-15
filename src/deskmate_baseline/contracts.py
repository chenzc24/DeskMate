"""Framework-neutral contracts shared by Baseline capture, inference, and UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


INTERNAL_LABELS: tuple[str, ...] = (
    "ragdoll",
    "singapura",
    "persian",
    "sphynx",
    "pallas",
    "not_target",
)
REPORTABLE_LABELS: tuple[str, ...] = INTERNAL_LABELS[:-1]


@dataclass(frozen=True, slots=True)
class FramePacket:
    """One captured frame with enough metadata to reject stale observations."""

    frame_id: int
    captured_at_ns: int
    image_bgr: Any
    source: str
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.frame_id < 0:
            raise ValueError("frame_id must be non-negative")
        if self.captured_at_ns <= 0:
            raise ValueError("captured_at_ns must be positive")
        if not self.source.strip():
            raise ValueError("source must be non-empty")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("frame dimensions must be positive")


@dataclass(frozen=True, slots=True)
class QualityResult:
    """Quality-gate result; thresholds remain provisional until Phase 3."""

    blur_score: float
    mean_brightness: float
    overexposed_ratio: float
    underexposed_ratio: float
    frame_age_ms: float
    roi_coverage: float
    valid: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ClassificationObservation:
    """Task-specific Baseline result produced at the model-runner boundary."""

    task: str
    label: str
    probabilities: tuple[float, ...]
    calibrated_confidence: float
    margin: float
    topk: tuple[tuple[str, float], ...]
    model_id: str
    roi_scale: str
    frame_id: int
    captured_at_ns: int
    inferred_at_ns: int
    valid: bool
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.task != "cat_breed":
            raise ValueError("Baseline task must be cat_breed")
        if self.label not in INTERNAL_LABELS:
            raise ValueError(f"unknown label: {self.label}")
        if len(self.probabilities) != len(INTERNAL_LABELS):
            raise ValueError("probabilities must follow the six-output order")
        if any(value < 0.0 or value > 1.0 for value in self.probabilities):
            raise ValueError("probabilities must be within [0, 1]")
        if self.valid and abs(sum(self.probabilities) - 1.0) > 1e-6:
            raise ValueError("valid probabilities must sum to 1")
        if not 0.0 <= self.calibrated_confidence <= 1.0:
            raise ValueError("calibrated_confidence must be within [0, 1]")
        if not 0.0 <= self.margin <= 1.0:
            raise ValueError("margin must be within [0, 1]")
        if self.inferred_at_ns < self.captured_at_ns:
            raise ValueError("inference cannot precede capture")
        if self.valid and self.reason is not None:
            raise ValueError("valid observation cannot have an invalid reason")
        if not self.valid and not self.reason:
            raise ValueError("invalid observation must explain its reason")

    @classmethod
    def invalid(
        cls,
        *,
        frame: FramePacket,
        model_id: str,
        roi_scale: str,
        inferred_at_ns: int,
        reason: str,
    ) -> "ClassificationObservation":
        return cls(
            task="cat_breed",
            label="not_target",
            probabilities=(0.0,) * len(INTERNAL_LABELS),
            calibrated_confidence=0.0,
            margin=0.0,
            topk=(),
            model_id=model_id,
            roi_scale=roi_scale,
            frame_id=frame.frame_id,
            captured_at_ns=frame.captured_at_ns,
            inferred_at_ns=inferred_at_ns,
            valid=False,
            reason=reason,
        )


@dataclass(frozen=True, slots=True)
class ConfirmationEvent:
    """A quality-gated, reportable census event."""

    event_id: str
    confirmed_at_ns: int
    species: str
    confidence: float
    margin: float
    found_count: int
    model_id: str

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError("event_id must be non-empty")
        if self.species not in REPORTABLE_LABELS:
            raise ValueError("only target species can produce confirmation events")
        if not 1 <= self.found_count <= 8:
            raise ValueError("found_count must be within the eight-target mission")
