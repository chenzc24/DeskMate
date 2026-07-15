"""Bounded OpenCV video consumer with explicit disconnect and reconnect state."""

from __future__ import annotations

import time
from typing import Any, Callable, Protocol

from ..domain.contracts import FramePacket


class CaptureLike(Protocol):
    def isOpened(self) -> bool: ...

    def read(self) -> tuple[bool, Any]: ...

    def release(self) -> None: ...


class OpenCVFrameSource:
    """Consume one endpoint without retry loops or stale-frame reuse."""

    def __init__(
        self,
        endpoint: int | str,
        *,
        capture_factory: Callable[[int | str], CaptureLike] | None = None,
        source_name: str | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.source_name = source_name or f"opencv:{endpoint}"
        self._capture_factory = capture_factory
        self._capture: CaptureLike | None = None
        self._next_frame_id = 0
        self._health = "closed"
        self.open_attempts = 0
        self.reconnect_attempts = 0
        self.read_failures = 0
        self.frames_read = 0

    def _factory(self, endpoint: int | str) -> CaptureLike:
        if self._capture_factory is not None:
            return self._capture_factory(endpoint)
        import cv2

        return cv2.VideoCapture(endpoint)

    def open(self) -> bool:
        self._release_capture()
        self.open_attempts += 1
        capture = self._factory(self.endpoint)
        if not capture.isOpened():
            capture.release()
            self._health = "open_failed"
            return False
        self._capture = capture
        self._health = "ready"
        return True

    def reconnect(self) -> bool:
        self.reconnect_attempts += 1
        return self.open()

    def read(self) -> FramePacket | None:
        if self._capture is None:
            self._health = "not_open"
            return None
        ok, image = self._capture.read()
        shape = getattr(image, "shape", ()) if ok else ()
        if not ok or len(shape) != 3 or int(shape[2]) != 3:
            self.read_failures += 1
            self._release_capture()
            self._health = "disconnected"
            return None
        captured_at_ns = time.time_ns()
        packet = FramePacket(
            frame_id=self._next_frame_id,
            captured_at_ns=captured_at_ns,
            image_bgr=image,
            source=self.source_name,
            width=int(shape[1]),
            height=int(shape[0]),
        )
        self._next_frame_id += 1
        self.frames_read += 1
        self._health = "ready"
        return packet

    def health(self) -> str:
        return self._health

    def status(self) -> dict[str, int | str | bool]:
        return {
            "health": self._health,
            "opened": self._capture is not None,
            "open_attempts": self.open_attempts,
            "reconnect_attempts": self.reconnect_attempts,
            "read_failures": self.read_failures,
            "frames_read": self.frames_read,
            "next_frame_id": self._next_frame_id,
        }

    def _release_capture(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def close(self) -> None:
        self._release_capture()
        self._health = "closed"

    def __enter__(self) -> "OpenCVFrameSource":
        if not self.open():
            raise RuntimeError(f"could not open video endpoint: {self.endpoint}")
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
