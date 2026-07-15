from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pytest

from deskmate_baseline.domain.contracts import REPORTABLE_LABELS, FramePacket
from deskmate_baseline.perception.inference import ClassMappingError
from deskmate_baseline.perception.target_inference import (
    UltralyticsTargetClassificationBackend,
    fuse_target_probabilities,
    target_index_mapping,
)


class FakeProbs:
    def __init__(self, values):
        self.data = values


class FakeResult:
    def __init__(self, values):
        self.probs = FakeProbs(values)


class FakeModel:
    def __init__(self, names, values=None):
        self.names = names
        self.values = values or [0.7, 0.1, 0.1, 0.05, 0.05]

    def predict(self, *, source, **_kwargs):
        return [FakeResult(self.values)]


def frame() -> FramePacket:
    return FramePacket(
        frame_id=4,
        captured_at_ns=time.time_ns(),
        image_bgr=np.zeros((100, 150, 3), dtype=np.uint8),
        source="fixture",
        width=150,
        height=100,
    )


def test_target_mapping_accepts_exact_five_breeds() -> None:
    names = {0: "4_pallas", 1: "0_ragdoll", 2: "2_persian", 3: "1_singapura", 4: "3_sphynx"}
    assert target_index_mapping(names) == (1, 3, 2, 4, 0)
    with pytest.raises(ClassMappingError, match="exactly five"):
        target_index_mapping(dict(enumerate((*REPORTABLE_LABELS, "not_target"))))


def test_target_backend_preserves_six_slot_contract(tmp_path: Path) -> None:
    checkpoint = tmp_path / "model.pt"
    checkpoint.write_bytes(b"fixture")
    fake = FakeModel({index: f"{index}_{label}" for index, label in enumerate(REPORTABLE_LABELS)})
    backend = UltralyticsTargetClassificationBackend(
        checkpoint=checkpoint, model_factory=lambda *_args, **_kwargs: fake
    )
    backend.load()
    observation = backend.infer(frame(), "wide")
    assert observation.valid
    assert observation.label == "ragdoll"
    assert len(observation.probabilities) == 6
    assert observation.probabilities[-1] == 0.0
    assert sum(observation.probabilities) == pytest.approx(1.0)


def test_fusion_keeps_rejection_outside_breed_head() -> None:
    fused = fuse_target_probabilities(
        [(0.7, 0.1, 0.1, 0.05, 0.05, 0.0), (0.3, 0.4, 0.1, 0.1, 0.1, 0.0)],
        weights=(2.0, 1.0),
    )
    assert fused[-1] == 0.0
    assert fused[0] > fused[1]
    assert sum(fused) == pytest.approx(1.0)
