"""Generate and consume a local fixture replay; never claim robot evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from deskmate_baseline.app.video import OpenCVFrameSource  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "downloads" / "phase1_candidates" / "offline_fixture_replay.mp4",
    )
    parser.add_argument("--frames-per-image", type=int, default=4)
    args = parser.parse_args()
    import cv2

    images = sorted((ROOT / "References" / "The requirement" / "SWS3009A_Assg_assets").glob("cat-*.png"))
    if not images:
        raise RuntimeError("assignment smoke images are missing")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(args.output), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (320, 240))
    if not writer.isOpened():
        raise RuntimeError("could not create fixture replay")
    written = 0
    try:
        for path in images:
            image = cv2.imread(str(path))
            if image is None:
                raise RuntimeError(f"could not decode {path}")
            canvas = cv2.resize(image, (320, 240))
            for _ in range(args.frames_per_image):
                writer.write(canvas)
                written += 1
    finally:
        writer.release()

    source = OpenCVFrameSource(str(args.output), source_name="offline_fixture")
    if not source.open():
        raise RuntimeError("could not reopen fixture replay")
    ids = []
    timestamps = []
    while True:
        packet = source.read()
        if packet is None:
            break
        ids.append(packet.frame_id)
        timestamps.append(packet.captured_at_ns)
        if packet.image_bgr.shape != (240, 320, 3):
            raise RuntimeError("unexpected replay frame shape")
    status_at_eof = source.status()
    source.close()
    report = {
        "schema_version": 1,
        "evidence_role": "offline_fixture_only",
        "real_robot_evidence": False,
        "motion_enabled": False,
        "frames_written": written,
        "frames_read": len(ids),
        "sequential_frame_ids": ids == list(range(len(ids))),
        "monotonic_timestamps": timestamps == sorted(timestamps),
        "eof_health": status_at_eof["health"],
        "read_failures": status_at_eof["read_failures"],
        "stale_frame_reused": len(ids) != written,
    }
    print(json.dumps(report, indent=2))
    return 0 if all((len(ids) == written, report["sequential_frame_ids"], report["monotonic_timestamps"])) else 3


if __name__ == "__main__":
    raise SystemExit(main())
