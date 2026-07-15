from __future__ import annotations

import pytest

from deskmate_baseline.domain.contracts import (
    ClassificationObservation,
    ConfirmationEvent,
    FramePacket,
)
from deskmate_baseline.app.runtime import (
    BoundedInferenceQueue,
    EventPresenter,
    InferenceJob,
    LatestFrameBuffer,
    TemporalState,
    aggregate_probabilities,
    evaluate_quality,
)


def frame(frame_id: int, captured_at_ns: int | None = None) -> FramePacket:
    return FramePacket(
        frame_id=frame_id,
        captured_at_ns=captured_at_ns or 1_000 + frame_id,
        image_bgr=b"frame",
        source="fixture",
        width=320,
        height=240,
    )


def observation(
    frame_id: int,
    probabilities: tuple[float, ...] = (0.7, 0.1, 0.05, 0.05, 0.05, 0.05),
) -> ClassificationObservation:
    ranked = sorted(
        zip(("ragdoll", "singapura", "persian", "sphynx", "pallas", "not_target"), probabilities),
        key=lambda item: item[1],
        reverse=True,
    )
    return ClassificationObservation(
        task="cat_breed",
        label=ranked[0][0],
        probabilities=probabilities,
        calibrated_confidence=ranked[0][1],
        margin=ranked[0][1] - ranked[1][1],
        topk=tuple(ranked[:3]),
        model_id="B-M01",
        roi_scale="medium",
        frame_id=frame_id,
        captured_at_ns=1_000 + frame_id,
        inferred_at_ns=2_000 + frame_id,
        valid=True,
    )


def test_latest_frame_buffer_is_bounded_and_counts_drops() -> None:
    buffer = LatestFrameBuffer(capacity=2)
    buffer.push(frame(1))
    buffer.push(frame(2))
    buffer.push(frame(3))
    assert buffer.latest().frame_id == 3
    assert buffer.dropped_frames == 1
    assert [item.frame_id for item in buffer.fresh_snapshot(count=2, now_ns=2_000, max_age_ns=2_000)] == [2, 3]


def test_confirmation_has_priority_and_preview_is_single_pending() -> None:
    queue = BoundedInferenceQueue(max_confirmation_jobs=1)
    queue.submit_preview(InferenceJob("p1", "preview", (frame(1),)))
    queue.submit_preview(InferenceJob("p2", "preview", (frame(2),)))
    assert queue.dropped_preview_jobs == 1
    assert queue.submit_confirmation(InferenceJob("c1", "confirmation", (frame(3),)))
    assert not queue.submit_confirmation(InferenceJob("c2", "confirmation", (frame(4),)))
    assert queue.rejected_confirmation_jobs == 1
    assert queue.pop_next().job_id == "c1"
    assert queue.pop_next().job_id == "p2"
    assert queue.pop_next() is None
    assert queue.sizes() == (0, 0)


def test_stale_observation_clears_temporal_state() -> None:
    state = TemporalState(capacity=7)
    obs = observation(1)
    assert state.add(obs, now_ns=2_001, max_age_ns=2_000)
    assert len(state) == 1
    assert not state.add(obs, now_ns=4_001, max_age_ns=2_000)
    assert len(state) == 0


def test_preview_is_quiet_and_confirmation_is_exactly_once() -> None:
    presenter = EventPresenter()
    payload = presenter.preview_payload(observation(1))
    assert payload["state"] == "STABLE"
    assert payload["console_line"] is None
    event = ConfirmationEvent(
        event_id="event-1",
        confirmed_at_ns=1_000_000_000,
        species="ragdoll",
        confidence=0.9,
        margin=0.8,
        found_count=1,
        model_id="B-M01",
    )
    line = presenter.confirmation_line(event)
    assert "CONFIRMED species=ragdoll" in line
    assert presenter.confirmation_line(event) is None


def test_probability_aggregation_uses_weighted_probabilities() -> None:
    first = observation(1, (0.6, 0.2, 0.05, 0.05, 0.05, 0.05))
    second = observation(2, (0.2, 0.7, 0.025, 0.025, 0.025, 0.025))
    aggregate = aggregate_probabilities(
        (first, second), weights=(3.0, 1.0), inferred_at_ns=9_000
    )
    assert aggregate.label == "ragdoll"
    assert aggregate.probabilities[0] == pytest.approx(0.5)
    assert aggregate.probabilities[1] == pytest.approx(0.325)


def test_quality_gate_reports_all_failure_reasons() -> None:
    result = evaluate_quality(
        blur_score=5.0,
        mean_brightness=10.0,
        overexposed_ratio=0.5,
        underexposed_ratio=0.5,
        frame_age_ms=501.0,
        roi_coverage=0.2,
        thresholds={
            "minimum_blur_score": 20.0,
            "minimum_mean_brightness": 20.0,
            "maximum_mean_brightness": 235.0,
            "maximum_overexposed_ratio": 0.35,
            "maximum_underexposed_ratio": 0.35,
            "maximum_frame_age_ms": 500.0,
            "minimum_roi_coverage": 0.5,
        },
    )
    assert not result.valid
    assert set(result.reasons) == {
        "blur",
        "underexposed_mean",
        "overexposed_ratio",
        "underexposed_ratio",
        "stale",
        "roi_coverage",
    }
