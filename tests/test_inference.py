from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pytest

from deskmate_baseline.contracts import INTERNAL_LABELS, FramePacket
from deskmate_baseline.inference import (
    ClassMappingError,
    UltralyticsClassificationBackend,
    canonical_index_mapping,
    extract_center_roi,
)


class FakeProbs:
    def __init__(self, values):
        self.data = values


class FakeResult:
    def __init__(self, values):
        self.probs = FakeProbs(values)
        self.boxes = object()


class FakeModel:
    def __init__(self, names, values=None, error=None):
        self.names = names
        self.values = values or [0.6, 0.1, 0.1, 0.05, 0.05, 0.1]
        self.error = error
        self.sources = []

    def predict(self, *, source, **_kwargs):
        self.sources.append(source)
        if self.error:
            raise self.error
        return [FakeResult(self.values)]


def frame(*, age_ms: float = 0.0) -> FramePacket:
    captured = time.time_ns() - int(age_ms * 1_000_000)
    return FramePacket(
        frame_id=1,
        captured_at_ns=captured,
        image_bgr=np.zeros((101, 151, 3), dtype=np.uint8),
        source="fixture",
        width=151,
        height=101,
    )


def test_mapping_accepts_indexed_names_and_reorders_native_indices() -> None:
    names = {
        0: "4_pallas", 1: "0_ragdoll", 2: "5_not_target",
        3: "2_persian", 4: "1_singapura", 5: "3_sphynx",
    }
    assert canonical_index_mapping(names) == (1, 4, 3, 5, 0, 2)


@pytest.mark.parametrize(
    "names",
    [
        {index: label for index, label in enumerate(INTERNAL_LABELS[:-1])},
        {index: label for index, label in enumerate((*INTERNAL_LABELS, "extra"))},
        {index: "ragdoll" for index in range(6)},
    ],
)
def test_mapping_rejects_missing_extra_or_duplicate_names(names) -> None:
    with pytest.raises(ClassMappingError):
        canonical_index_mapping(names)


def test_centre_roi_is_bounded_and_copied() -> None:
    image = np.arange(7 * 9 * 3, dtype=np.uint8).reshape(7, 9, 3)
    roi = extract_center_roi(image, 0.6)
    assert roi.shape == (4, 5, 3)
    assert not np.shares_memory(image, roi)
    assert extract_center_roi(image, 1.0).shape == image.shape
    with pytest.raises(ValueError):
        extract_center_roi(image, 0.0)


def test_backend_contains_native_result_and_emits_contract(tmp_path: Path) -> None:
    checkpoint = tmp_path / "model.pt"
    checkpoint.write_bytes(b"fixture")
    fake = FakeModel({index: f"{index}_{label}" for index, label in enumerate(INTERNAL_LABELS)})
    backend = UltralyticsClassificationBackend(
        checkpoint=checkpoint, model_factory=lambda *_args, **_kwargs: fake
    )
    backend.load()
    observation = backend.infer(frame(), "medium")
    assert observation.valid
    assert observation.label == "ragdoll"
    assert observation.topk[0][0] == "ragdoll"
    assert sum(observation.probabilities) == pytest.approx(1.0)
    assert fake.sources[0].shape == (81, 121, 3)
    assert not hasattr(observation, "probs")


def test_backend_rejects_stale_frame_without_calling_model(tmp_path: Path) -> None:
    checkpoint = tmp_path / "model.pt"
    checkpoint.write_bytes(b"fixture")
    fake = FakeModel(dict(enumerate(INTERNAL_LABELS)))
    backend = UltralyticsClassificationBackend(
        checkpoint=checkpoint, model_factory=lambda *_args, **_kwargs: fake
    )
    backend.load()
    observation = backend.infer(frame(age_ms=1000), "wide")
    assert not observation.valid
    assert observation.reason == "stale_frame"
    assert fake.sources == []


def test_backend_converts_inference_exception_to_invalid_observation(tmp_path: Path) -> None:
    checkpoint = tmp_path / "model.pt"
    checkpoint.write_bytes(b"fixture")
    fake = FakeModel(dict(enumerate(INTERNAL_LABELS)), error=RuntimeError("boom"))
    backend = UltralyticsClassificationBackend(
        checkpoint=checkpoint, model_factory=lambda *_args, **_kwargs: fake
    )
    backend.load()
    observation = backend.infer(frame(), "tight")
    assert not observation.valid
    assert "inference_error:RuntimeError:boom" == observation.reason
    assert backend.health() == observation.reason


def test_backend_rejects_frame_dimension_mismatch(tmp_path: Path) -> None:
    checkpoint = tmp_path / "model.pt"
    checkpoint.write_bytes(b"fixture")
    fake = FakeModel(dict(enumerate(INTERNAL_LABELS)))
    backend = UltralyticsClassificationBackend(
        checkpoint=checkpoint, model_factory=lambda *_args, **_kwargs: fake
    )
    backend.load()
    mismatched = frame()
    object.__setattr__(mismatched, "width", 999)
    observation = backend.infer(mismatched, "wide")
    assert not observation.valid
    assert "frame metadata does not match image dimensions" in observation.reason
    assert fake.sources == []


def test_backend_load_rejects_imagenet_like_mapping(tmp_path: Path) -> None:
    checkpoint = tmp_path / "model.pt"
    checkpoint.write_bytes(b"fixture")
    fake = FakeModel({index: f"imagenet_{index}" for index in range(1000)})
    backend = UltralyticsClassificationBackend(
        checkpoint=checkpoint, model_factory=lambda *_args, **_kwargs: fake
    )
    with pytest.raises(ClassMappingError, match="exactly six"):
        backend.load()
    assert backend.health().startswith("load_error:ClassMappingError")
