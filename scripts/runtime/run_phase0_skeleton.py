"""Run the bounded Phase 0 contracts on a local PNG/JPEG smoke-test frame."""

from __future__ import annotations

import argparse
import json
import sys
import time
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from deskmate_baseline.domain.contracts import (  # noqa: E402
    ClassificationObservation,
    ConfirmationEvent,
    FramePacket,
)
from deskmate_baseline.domain.media import probe_image_size  # noqa: E402
from deskmate_baseline.app.runtime import (  # noqa: E402
    BoundedInferenceQueue,
    EventPresenter,
    InferenceJob,
    LatestFrameBuffer,
    TemporalState,
)


def placeholder_observation(frame: FramePacket, inferred_at_ns: int) -> ClassificationObservation:
    probabilities = (0.82, 0.05, 0.04, 0.03, 0.02, 0.04)
    return ClassificationObservation(
        task="cat_breed",
        label="ragdoll",
        probabilities=probabilities,
        calibrated_confidence=0.82,
        margin=0.77,
        topk=(("ragdoll", 0.82), ("singapura", 0.05), ("persian", 0.04)),
        model_id="B-M01-PLACEHOLDER",
        roi_scale="medium",
        frame_id=frame.frame_id,
        captured_at_ns=frame.captured_at_ns,
        inferred_at_ns=inferred_at_ns,
        valid=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument(
        "--source-kind",
        choices=("assignment_smoke", "recorded_robot", "live_robot"),
        default="assignment_smoke",
    )
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs" / "baseline_phase0.toml"
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    with args.config.open("rb") as handle:
        config = tomllib.load(handle)
    data = args.image.read_bytes()
    width, height, image_format = probe_image_size(data)
    captured_at_ns = time.time_ns()
    frame = FramePacket(
        frame_id=0,
        captured_at_ns=captured_at_ns,
        image_bgr=data,
        source=f"{args.source_kind}:{args.image}",
        width=width,
        height=height,
    )

    buffer = LatestFrameBuffer(config["capture"]["latest_frame_capacity"])
    buffer.push(frame)
    queue = BoundedInferenceQueue(config["inference_queue"]["max_confirmation_jobs"])
    queue.submit_preview(InferenceJob("preview-0", "preview", (frame,)))
    queue.submit_confirmation(InferenceJob("confirmation-0", "confirmation", (frame,)))
    first_job = queue.pop_next()
    second_job = queue.pop_next()

    inferred_at_ns = max(time.time_ns(), captured_at_ns)
    observation = placeholder_observation(frame, inferred_at_ns)
    presenter = EventPresenter()
    preview = presenter.preview_payload(observation)
    event = ConfirmationEvent(
        event_id="phase0-confirmation-0",
        confirmed_at_ns=inferred_at_ns,
        species=observation.label,
        confidence=observation.calibrated_confidence,
        margin=observation.margin,
        found_count=1,
        model_id=observation.model_id,
    )
    confirmation_line = presenter.confirmation_line(event)
    duplicate_line = presenter.confirmation_line(event)

    temporal = TemporalState()
    accepted_fresh = temporal.add(
        observation,
        now_ns=inferred_at_ns,
        max_age_ns=config["capture"]["max_frame_age_ms"] * 1_000_000,
    )
    temporal.add(
        observation,
        now_ns=inferred_at_ns
        + (config["capture"]["max_frame_age_ms"] + 1) * 1_000_000,
        max_age_ns=config["capture"]["max_frame_age_ms"] * 1_000_000,
    )

    report = {
        "schema_version": 1,
        "input": {
            "path": str(args.image),
            "source_kind": args.source_kind,
            "width": width,
            "height": height,
            "format": image_format,
            "real_robot_evidence": args.source_kind in {"recorded_robot", "live_robot"},
        },
        "contracts": {
            "first_job_kind": first_job.kind if first_job else None,
            "second_job_kind": second_job.kind if second_job else None,
            "preview_console_line": preview["console_line"],
            "confirmation_line": confirmation_line,
            "duplicate_confirmation_line": duplicate_line,
            "fresh_observation_accepted": accepted_fresh,
            "temporal_size_after_stale": len(temporal),
            "queue_sizes_after_pop": queue.sizes(),
            "motion_enabled": config["robot"]["motion_enabled"],
        },
        "placeholder_only": True,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
