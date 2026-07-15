from __future__ import annotations

import pytest

from deskmate_baseline.domain.contracts import (
    INTERNAL_LABELS,
    REPORTABLE_LABELS,
    ClassificationObservation,
    ConfirmationEvent,
    FramePacket,
)


def make_frame() -> FramePacket:
    return FramePacket(
        frame_id=7,
        captured_at_ns=1_000,
        image_bgr=b"opaque-frame",
        source="fixture",
        width=640,
        height=480,
    )


def test_canonical_label_order_is_frozen() -> None:
    assert INTERNAL_LABELS == (
        "ragdoll",
        "singapura",
        "persian",
        "sphynx",
        "pallas",
        "not_target",
    )
    assert REPORTABLE_LABELS == INTERNAL_LABELS[:-1]


def test_invalid_observation_requires_reason_and_six_outputs() -> None:
    frame = make_frame()
    observation = ClassificationObservation.invalid(
        frame=frame,
        model_id="B-M01-PLACEHOLDER",
        roi_scale="medium",
        inferred_at_ns=2_000,
        reason="stale",
    )
    assert not observation.valid
    assert observation.reason == "stale"
    assert len(observation.probabilities) == 6


def test_valid_observation_rejects_wrong_probability_shape() -> None:
    with pytest.raises(ValueError, match="six-output"):
        ClassificationObservation(
            task="cat_breed",
            label="ragdoll",
            probabilities=(0.9, 0.1),
            calibrated_confidence=0.9,
            margin=0.8,
            topk=(("ragdoll", 0.9),),
            model_id="B-M01",
            roi_scale="medium",
            frame_id=1,
            captured_at_ns=1,
            inferred_at_ns=2,
            valid=True,
        )


def test_not_target_cannot_become_confirmation_event() -> None:
    with pytest.raises(ValueError, match="target species"):
        ConfirmationEvent(
            event_id="event-1",
            confirmed_at_ns=1_000,
            species="not_target",
            confidence=0.99,
            margin=0.9,
            found_count=1,
            model_id="B-M01",
        )
