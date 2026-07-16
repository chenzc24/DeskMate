"""Run BD05 + M9 on a live MJPEG stream, video file, or local camera.

This is an inference-only entry point.  It never sends motion commands to the
robot; each completed frame produces a JSON result on stdout and can optionally
be written to a latest-result file or POSTed to another service.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import tomllib
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from deskmate_baseline.app.runtime import (  # noqa: E402
    TemporalState,
    aggregate_probabilities,
)
from deskmate_baseline.app.video import OpenCVFrameSource  # noqa: E402
from deskmate_baseline.domain.contracts import FramePacket  # noqa: E402
from deskmate_baseline.perception.localization import (  # noqa: E402
    UltralyticsCatLocalizerBackend,
    route_classification_roi,
)
from deskmate_baseline.perception.target_inference import (  # noqa: E402
    UltralyticsTargetClassificationBackend,
)


def parse_source(value: str) -> int | str:
    """Keep numeric camera indexes convenient without changing URL/path inputs."""
    return int(value) if value.isdecimal() else value


def observation_payload(observation: Any) -> dict[str, Any]:
    return {
        "valid": observation.valid,
        "reason": observation.reason,
        "label": observation.label,
        "confidence": round(observation.calibrated_confidence, 6),
        "margin": round(observation.margin, 6),
        "topk": [
            {"label": label, "confidence": round(confidence, 6)}
            for label, confidence in observation.topk
        ],
    }


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def post_result(url: str, payload: dict[str, Any], timeout_seconds: float) -> str | None:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            if 200 <= response.status < 300:
                return None
            return f"callback_http_{response.status}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return f"callback_error:{type(exc).__name__}:{exc}"


def render_assisted_view(
    *,
    frame: FramePacket,
    detector: Any,
    routed: Any,
    classifier: Any,
    stable: Any | None,
    maximum_width: int,
) -> bool:
    """Show detector boxes, the routed ROI, and M9's current classification.

    Green rectangles are raw BD05 detections.  The blue rectangle is the padded
    detector crop sent to M9.  A yellow rectangle means BD05 missed and M9 is
    classifying the configured centre fallback, not a detected cat.
    """
    import cv2

    image = frame.image_bgr.copy()
    height, width = image.shape[:2]
    for index, box in enumerate(detector.boxes, start=1):
        x1, y1, x2, y2 = box.xyxy
        left, top = int(x1 * width), int(y1 * height)
        right, bottom = int(x2 * width), int(y2 * height)
        cv2.rectangle(image, (left, top), (right, bottom), (0, 220, 0), 3)
        cv2.putText(
            image,
            f"BD05 CAT {index}: {box.confidence:.1%}",
            (left, max(28, top - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 220, 0),
            2,
            cv2.LINE_AA,
        )

    left, top, right, bottom = routed.pixel_xyxy
    fallback = routed.mode == "centre_fallback"
    roi_colour = (0, 215, 255) if fallback else (255, 170, 0)
    cv2.rectangle(image, (left, top), (right, bottom), roi_colour, 2)
    route_name = "CENTRE FALLBACK (NO BD05 BOX)" if fallback else "M9 PADDED ROI"
    current = f"M9 {classifier.label}: {classifier.calibrated_confidence:.1%}"
    stable_text = (
        f" | vote {stable.label}: {stable.calibrated_confidence:.1%}"
        if stable is not None
        else " | collecting vote"
    )
    cv2.putText(
        image,
        f"{route_name} | {current}{stable_text}",
        (12, height - 18),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        roi_colour,
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        image,
        "DeskMate live inference  |  press Q in this window to stop",
        (12, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    if width > maximum_width:
        scale = maximum_width / width
        image = cv2.resize(image, (maximum_width, int(round(height * scale))))
    cv2.imshow("DeskMate live inference", image)
    return (cv2.waitKey(1) & 0xFF) != ord("q")


def build_result(
    *,
    frame: FramePacket,
    detector: Any,
    routed: Any,
    classifier: Any,
    stable: Any | None,
    temporal_size: int,
    source_status: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "deskmate_robot_inference",
        "motion_enabled": False,
        "frame": {
            "id": frame.frame_id,
            "captured_at_ns": frame.captured_at_ns,
            "width": frame.width,
            "height": frame.height,
            "source": frame.source,
        },
        "detector": {
            "valid": detector.valid,
            "reason": detector.reason,
            "boxes": [
                {
                    "xyxy_normalized": [round(value, 6) for value in box.xyxy],
                    "confidence": round(box.confidence, 6),
                    "area_ratio": round(box.area_ratio, 6),
                }
                for box in detector.boxes
            ],
        },
        "roi": {
            "mode": routed.mode,
            "reason": routed.route_reason,
            "pixel_xyxy": list(routed.pixel_xyxy),
            "detector_confidence": routed.source_confidence,
        },
        "instant": observation_payload(classifier),
        "temporal_vote": {
            "frames": temporal_size,
            "ready": stable is not None,
            "result": observation_payload(stable) if stable is not None else None,
        },
        "stream": source_status,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        required=True,
        help="MJPEG URL, video-file path, or numeric OpenCV camera index",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "models" / "frozen" / "baseline-bd05-m09.toml",
    )
    parser.add_argument("--device", default="0", help="Ultralytics device, e.g. 0 or cpu")
    parser.add_argument("--vote-window", type=int, default=5)
    parser.add_argument("--max-frame-age-ms", type=float, default=500.0)
    parser.add_argument("--max-frames", type=int, default=0, help="0 means run until Ctrl+C")
    parser.add_argument("--reconnect-seconds", type=float, default=2.0)
    parser.add_argument("--result-file", type=Path)
    parser.add_argument("--callback-url")
    parser.add_argument("--callback-timeout-seconds", type=float, default=1.0)
    parser.add_argument("--display", action="store_true", help="show annotated live video")
    parser.add_argument("--display-max-width", type=int, default=1280)
    args = parser.parse_args()

    if args.vote_window <= 0:
        parser.error("--vote-window must be positive")
    if args.max_frames < 0:
        parser.error("--max-frames must be zero or positive")
    if args.reconnect_seconds <= 0:
        parser.error("--reconnect-seconds must be positive")
    if args.max_frame_age_ms <= 0:
        parser.error("--max-frame-age-ms must be positive")
    if args.display_max_width <= 0:
        parser.error("--display-max-width must be positive")

    with args.config.open("rb") as handle:
        config = tomllib.load(handle)
    detector_config = config["detector"]
    classifier_config = config["classifier"]
    routing_config = config["routing"]
    device: int | str = int(args.device) if args.device.isdecimal() else args.device

    detector = UltralyticsCatLocalizerBackend(
        checkpoint=ROOT / detector_config["checkpoint"],
        model_id=detector_config["model_id"],
        device=device,
        imgsz=int(detector_config["imgsz"]),
        confidence_threshold=float(detector_config["confidence_threshold"]),
        minimum_box_area_ratio=float(detector_config["minimum_box_area_ratio"]),
    )
    classifier = UltralyticsTargetClassificationBackend(
        checkpoint=ROOT / classifier_config["checkpoint"],
        model_id=classifier_config["model_id"],
        device=device,
        imgsz=int(classifier_config["imgsz"]),
        temperature=float(classifier_config["temperature"]),
    )
    temporal = TemporalState(capacity=args.vote_window)
    source = OpenCVFrameSource(parse_source(args.source), source_name=args.source)

    detector.load()
    classifier.load()
    detector.warmup()
    classifier.warmup()
    processed = 0
    display_running = True
    try:
        while display_running and (args.max_frames == 0 or processed < args.max_frames):
            if not source.open():
                print(json.dumps({"kind": "stream_error", "error": "open_failed", "stream": source.status()}), flush=True)
                time.sleep(args.reconnect_seconds)
                continue
            while display_running and (args.max_frames == 0 or processed < args.max_frames):
                frame = source.read()
                if frame is None:
                    temporal.invalidate_missing_frame()
                    print(json.dumps({"kind": "stream_error", "error": "disconnected", "stream": source.status()}), flush=True)
                    break
                localized = detector.infer(frame)
                routed = route_classification_roi(
                    frame,
                    localized,
                    box_is_stable=bool(localized.valid and localized.boxes),
                    padding_ratio=float(routing_config["padding_ratio"]),
                    fallback_center_scale=float(routing_config["fallback_center_scale"]),
                    minimum_padded_short_side_pixels=int(routing_config["minimum_padded_short_side_pixels"]),
                )
                roi = FramePacket(
                    frame_id=frame.frame_id,
                    captured_at_ns=frame.captured_at_ns,
                    image_bgr=routed.image_bgr,
                    source=f"{frame.source}:{routed.mode}",
                    width=int(routed.image_bgr.shape[1]),
                    height=int(routed.image_bgr.shape[0]),
                )
                classified = classifier.infer(roi, "wide")
                accepted = temporal.add(
                    classified,
                    now_ns=time.time_ns(),
                    max_age_ns=int(args.max_frame_age_ms * 1_000_000),
                )
                stable = None
                if accepted and len(temporal) == args.vote_window:
                    observations = temporal.snapshot()
                    stable = aggregate_probabilities(observations, inferred_at_ns=time.time_ns())
                payload = build_result(
                    frame=frame,
                    detector=localized,
                    routed=routed,
                    classifier=classified,
                    stable=stable,
                    temporal_size=len(temporal),
                    source_status=source.status(),
                )
                if args.callback_url:
                    payload["callback_error"] = post_result(
                        args.callback_url, payload, args.callback_timeout_seconds
                    )
                if args.result_file:
                    atomic_write_json(args.result_file, payload)
                print(json.dumps(payload, ensure_ascii=False), flush=True)
                if args.display:
                    display_running = render_assisted_view(
                        frame=frame,
                        detector=localized,
                        routed=routed,
                        classifier=classified,
                        stable=stable,
                        maximum_width=args.display_max_width,
                    )
                processed += 1
            source.close()
            if display_running and args.max_frames == 0:
                time.sleep(args.reconnect_seconds)
    except KeyboardInterrupt:
        return 0
    finally:
        source.close()
        detector.close()
        classifier.close()
        if args.display:
            import cv2

            cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
