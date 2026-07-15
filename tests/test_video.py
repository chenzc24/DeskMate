from __future__ import annotations

import numpy as np

from deskmate_baseline.video import OpenCVFrameSource


class FakeCapture:
    def __init__(self, frames, *, opened=True):
        self.frames = list(frames)
        self.opened = opened
        self.released = False

    def isOpened(self):
        return self.opened

    def read(self):
        if not self.frames:
            return False, None
        return True, self.frames.pop(0)

    def release(self):
        self.released = True


def test_video_source_reads_fresh_packets_and_never_reuses_eof_frame() -> None:
    first = np.zeros((20, 30, 3), dtype=np.uint8)
    second = np.ones((10, 15, 3), dtype=np.uint8)
    capture = FakeCapture([first, second])
    source = OpenCVFrameSource("fixture.mp4", capture_factory=lambda _endpoint: capture)
    assert source.open()
    one = source.read()
    two = source.read()
    assert (one.frame_id, two.frame_id) == (0, 1)
    assert (one.width, one.height) == (30, 20)
    assert two.captured_at_ns >= one.captured_at_ns
    assert source.read() is None
    assert source.health() == "disconnected"
    assert capture.released
    assert source.read() is None
    assert source.health() == "not_open"
    assert source.status()["frames_read"] == 2


def test_video_source_reconnect_is_explicit_and_preserves_frame_ids() -> None:
    captures = [
        FakeCapture([], opened=False),
        FakeCapture([np.zeros((5, 6, 3), dtype=np.uint8)]),
    ]
    source = OpenCVFrameSource(0, capture_factory=lambda _endpoint: captures.pop(0))
    assert not source.open()
    assert source.health() == "open_failed"
    assert source.reconnect()
    assert source.read().frame_id == 0
    status = source.status()
    assert status["open_attempts"] == 2
    assert status["reconnect_attempts"] == 1


def test_video_source_rejects_non_bgr_frame_and_closes() -> None:
    capture = FakeCapture([np.zeros((10, 10), dtype=np.uint8)])
    source = OpenCVFrameSource("bad", capture_factory=lambda _endpoint: capture)
    assert source.open()
    assert source.read() is None
    assert source.status()["read_failures"] == 1
    source.close()
    assert source.health() == "closed"
