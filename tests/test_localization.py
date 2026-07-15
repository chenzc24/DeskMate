from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pytest

from deskmate_baseline.contracts import FramePacket
from deskmate_baseline.localization import (
    LocalizerMappingError,
    UltralyticsCatLocalizerBackend,
    resolve_native_class_id,
    route_classification_roi,
)


class FakeBoxes:
    def __init__(self, xyxyn=(), conf=(), cls=()):
        self.xyxyn = np.asarray(xyxyn, dtype=float).reshape((-1, 4))
        self.conf = np.asarray(conf, dtype=float)
        self.cls = np.asarray(cls, dtype=float)


class FakeResult:
    def __init__(self, boxes):
        self.boxes = boxes
        self.probs = object()


class FakeModel:
    def __init__(self, boxes=None, error=None):
        self.names = {0: "person", 15: "cat", 16: "dog"}
        self.boxes = boxes if boxes is not None else FakeBoxes()
        self.error = error
        self.calls = []

    def predict(self, *, source, **kwargs):
        self.calls.append((source, kwargs))
        if self.error:
            raise self.error
        return [FakeResult(self.boxes)]


def frame(*, age_ms=0.0):
    image = np.zeros((100, 200, 3), dtype=np.uint8)
    return FramePacket(
        frame_id=7,
        captured_at_ns=time.time_ns() - int(age_ms * 1_000_000),
        image_bgr=image,
        source="fixture",
        width=200,
        height=100,
    )


def backend(tmp_path: Path, fake: FakeModel, **kwargs):
    checkpoint = tmp_path / "detector.pt"
    checkpoint.write_bytes(b"fixture")
    result = UltralyticsCatLocalizerBackend(
        checkpoint=checkpoint,
        model_factory=lambda *_args, **_kwargs: fake,
        **kwargs,
    )
    result.load()
    return result


def test_resolves_cat_id_without_hardcoding_position():
    assert resolve_native_class_id({16: "dog", 15: "Cat"}) == 15
    with pytest.raises(LocalizerMappingError):
        resolve_native_class_id({0: "dog"})
    with pytest.raises(LocalizerMappingError):
        resolve_native_class_id({1: "cat", 2: "CAT"})


def test_adapter_filters_sorts_and_contains_native_results(tmp_path):
    fake = FakeModel(
        FakeBoxes(
            xyxyn=[[0.1, 0.1, 0.6, 0.8], [0.2, 0.2, 0.3, 0.3], [0, 0, 1, 1]],
            conf=[0.7, 0.95, 0.99],
            cls=[15, 15, 16],
        )
    )
    model = backend(tmp_path, fake, minimum_box_area_ratio=0.02)
    observation = model.infer(frame())
    assert observation.valid
    assert len(observation.boxes) == 1
    assert observation.boxes[0].confidence == pytest.approx(0.7)
    assert observation.boxes[0].native_class_id == 15
    assert not hasattr(observation, "results")
    assert fake.calls[0][1]["classes"] == [15]


def test_empty_detection_is_valid_and_routes_to_centre(tmp_path):
    model = backend(tmp_path, FakeModel())
    packet = frame()
    observation = model.infer(packet)
    routed = route_classification_roi(packet, observation, box_is_stable=True)
    assert observation.valid and observation.boxes == ()
    assert routed.mode == "centre_fallback"
    assert routed.image_bgr.shape == (80, 160, 3)


def test_stale_or_wrong_frame_never_routes_detector_crop(tmp_path):
    boxes = FakeBoxes([[0.1, 0.1, 0.6, 0.8]], [0.8], [15])
    model = backend(tmp_path, FakeModel(boxes))
    stale = model.infer(frame(age_ms=1000))
    assert not stale.valid and stale.reason == "stale_frame"

    packet = frame()
    observation = model.infer(packet)
    other = frame()
    object.__setattr__(other, "frame_id", packet.frame_id + 1)
    assert route_classification_roi(other, observation, box_is_stable=True).mode == "centre_fallback"
    assert route_classification_roi(packet, observation, box_is_stable=False).mode == "centre_fallback"


def test_stable_box_is_padded_clamped_and_copied(tmp_path):
    boxes = FakeBoxes([[0.0, 0.1, 0.9, 0.9]], [0.8], [15])
    model = backend(tmp_path, FakeModel(boxes))
    packet = frame()
    observation = model.infer(packet)
    routed = route_classification_roi(
        packet, observation, box_is_stable=True, padding_ratio=0.2
    )
    assert routed.mode == "detector_crop"
    assert routed.pixel_xyxy == (0, 0, 200, 100)
    assert routed.source_confidence == pytest.approx(0.8)
    assert not np.shares_memory(packet.image_bgr, routed.image_bgr)


def test_malformed_result_and_inference_error_fail_closed(tmp_path):
    malformed = FakeModel()
    malformed.boxes = None
    observation = backend(tmp_path, malformed).infer(frame())
    assert not observation.valid
    assert "missing Results.boxes" in observation.reason

    failed = backend(tmp_path, FakeModel(error=RuntimeError("boom"))).infer(frame())
    assert not failed.valid
    assert failed.reason == "inference_error:RuntimeError:boom"
