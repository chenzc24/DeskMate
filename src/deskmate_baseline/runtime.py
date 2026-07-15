"""Bounded Phase 0 scheduling, aggregation, and presentation primitives."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Generic, Protocol, TypeVar

from .contracts import (
    INTERNAL_LABELS,
    REPORTABLE_LABELS,
    ClassificationObservation,
    ConfirmationEvent,
    FramePacket,
    QualityResult,
)


OutputT = TypeVar("OutputT")


class ModelRunner(Protocol, Generic[OutputT]):
    def load(self) -> None: ...

    def warmup(self) -> None: ...

    def infer(self, frame: FramePacket, roi_scale: str) -> OutputT: ...

    def health(self) -> str: ...

    def close(self) -> None: ...


class LatestFrameBuffer:
    """Thread-safe bounded ring that never blocks capture on inference."""

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self._frames: deque[FramePacket] = deque(maxlen=capacity)
        self._lock = Lock()
        self.dropped_frames = 0

    @property
    def capacity(self) -> int:
        return self._frames.maxlen or 0

    def push(self, frame: FramePacket) -> None:
        with self._lock:
            if len(self._frames) == self.capacity:
                self.dropped_frames += 1
            self._frames.append(frame)

    def latest(self) -> FramePacket | None:
        with self._lock:
            return self._frames[-1] if self._frames else None

    def fresh_snapshot(
        self, *, count: int, now_ns: int, max_age_ns: int
    ) -> tuple[FramePacket, ...]:
        with self._lock:
            fresh = [
                frame
                for frame in self._frames
                if 0 <= now_ns - frame.captured_at_ns <= max_age_ns
            ]
            return tuple(fresh[-count:])


@dataclass(frozen=True, slots=True)
class InferenceJob:
    job_id: str
    kind: str
    frames: tuple[FramePacket, ...]

    def __post_init__(self) -> None:
        if self.kind not in {"preview", "confirmation"}:
            raise ValueError("job kind must be preview or confirmation")
        if not self.frames:
            raise ValueError("inference job requires at least one frame")


class BoundedInferenceQueue:
    """Confirmation-first queue with one replaceable preview slot."""

    def __init__(self, max_confirmation_jobs: int = 2) -> None:
        if max_confirmation_jobs <= 0:
            raise ValueError("max_confirmation_jobs must be positive")
        self._confirmations: deque[InferenceJob] = deque()
        self._max_confirmations = max_confirmation_jobs
        self._preview: InferenceJob | None = None
        self._lock = Lock()
        self.dropped_preview_jobs = 0
        self.rejected_confirmation_jobs = 0

    def submit_preview(self, job: InferenceJob) -> None:
        if job.kind != "preview":
            raise ValueError("submit_preview requires a preview job")
        with self._lock:
            if self._preview is not None:
                self.dropped_preview_jobs += 1
            self._preview = job

    def submit_confirmation(self, job: InferenceJob) -> bool:
        if job.kind != "confirmation":
            raise ValueError("submit_confirmation requires a confirmation job")
        with self._lock:
            if len(self._confirmations) >= self._max_confirmations:
                self.rejected_confirmation_jobs += 1
                return False
            self._confirmations.append(job)
            return True

    def pop_next(self) -> InferenceJob | None:
        with self._lock:
            if self._confirmations:
                return self._confirmations.popleft()
            preview = self._preview
            self._preview = None
            return preview

    def sizes(self) -> tuple[int, int]:
        with self._lock:
            return len(self._confirmations), int(self._preview is not None)


class TemporalState:
    """Small observation window that is invalidated by stale/missing input."""

    def __init__(self, capacity: int = 7) -> None:
        self._observations: deque[ClassificationObservation] = deque(maxlen=capacity)

    def add(
        self,
        observation: ClassificationObservation,
        *,
        now_ns: int,
        max_age_ns: int,
    ) -> bool:
        age_ns = now_ns - observation.captured_at_ns
        if not observation.valid or age_ns < 0 or age_ns > max_age_ns:
            self.clear()
            return False
        self._observations.append(observation)
        return True

    def invalidate_missing_frame(self) -> None:
        self.clear()

    def clear(self) -> None:
        self._observations.clear()

    def __len__(self) -> int:
        return len(self._observations)


def evaluate_quality(
    *,
    blur_score: float,
    mean_brightness: float,
    overexposed_ratio: float,
    underexposed_ratio: float,
    frame_age_ms: float,
    roi_coverage: float,
    thresholds: dict[str, float],
) -> QualityResult:
    reasons: list[str] = []
    if blur_score < thresholds["minimum_blur_score"]:
        reasons.append("blur")
    if mean_brightness < thresholds["minimum_mean_brightness"]:
        reasons.append("underexposed_mean")
    if mean_brightness > thresholds["maximum_mean_brightness"]:
        reasons.append("overexposed_mean")
    if overexposed_ratio > thresholds["maximum_overexposed_ratio"]:
        reasons.append("overexposed_ratio")
    if underexposed_ratio > thresholds["maximum_underexposed_ratio"]:
        reasons.append("underexposed_ratio")
    if frame_age_ms > thresholds["maximum_frame_age_ms"]:
        reasons.append("stale")
    if roi_coverage < thresholds["minimum_roi_coverage"]:
        reasons.append("roi_coverage")
    return QualityResult(
        blur_score=blur_score,
        mean_brightness=mean_brightness,
        overexposed_ratio=overexposed_ratio,
        underexposed_ratio=underexposed_ratio,
        frame_age_ms=frame_age_ms,
        roi_coverage=roi_coverage,
        valid=not reasons,
        reasons=tuple(reasons),
    )


def aggregate_probabilities(
    observations: tuple[ClassificationObservation, ...],
    *,
    weights: tuple[float, ...] | None = None,
    inferred_at_ns: int,
) -> ClassificationObservation:
    valid = tuple(observation for observation in observations if observation.valid)
    if not valid:
        raise ValueError("at least one valid observation is required")
    if weights is None:
        weights = (1.0,) * len(valid)
    if len(weights) != len(valid) or any(weight <= 0 for weight in weights):
        raise ValueError("weights must be positive and match valid observations")
    total_weight = sum(weights)
    probabilities = tuple(
        sum(obs.probabilities[index] * weight for obs, weight in zip(valid, weights))
        / total_weight
        for index in range(len(INTERNAL_LABELS))
    )
    ranked = sorted(
        zip(INTERNAL_LABELS, probabilities), key=lambda item: item[1], reverse=True
    )
    label, confidence = ranked[0]
    margin = confidence - ranked[1][1]
    newest = max(valid, key=lambda observation: observation.captured_at_ns)
    return ClassificationObservation(
        task="cat_breed",
        label=label,
        probabilities=probabilities,
        calibrated_confidence=confidence,
        margin=margin,
        topk=tuple(ranked[:3]),
        model_id=newest.model_id,
        roi_scale="aggregated",
        frame_id=newest.frame_id,
        captured_at_ns=newest.captured_at_ns,
        inferred_at_ns=inferred_at_ns,
        valid=True,
    )


class EventPresenter:
    """Separates quiet preview UI state from exactly-once console confirmation."""

    def __init__(self) -> None:
        self._printed_event_ids: set[str] = set()

    def preview_payload(self, observation: ClassificationObservation) -> dict[str, object]:
        state = "UNKNOWN"
        if observation.valid:
            state = "SEARCHING" if observation.label == "not_target" else "STABLE"
        return {
            "state": state,
            "label": observation.label,
            "confidence": observation.calibrated_confidence,
            "margin": observation.margin,
            "console_line": None,
        }

    def confirmation_line(self, event: ConfirmationEvent) -> str | None:
        if event.event_id in self._printed_event_ids:
            return None
        if event.species not in REPORTABLE_LABELS:
            raise ValueError("not_target cannot be printed as a species")
        self._printed_event_ids.add(event.event_id)
        timestamp = datetime.fromtimestamp(
            event.confirmed_at_ns / 1_000_000_000, tz=timezone.utc
        ).astimezone().isoformat(timespec="seconds")
        return (
            f"{timestamp} CONFIRMED species={event.species} "
            f"confidence={event.confidence:.3f} margin={event.margin:.3f} "
            f"found={event.found_count}/8 model={event.model_id}"
        )
