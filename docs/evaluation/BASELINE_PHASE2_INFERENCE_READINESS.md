# Baseline Phase 2 Inference Readiness

Status: **adapter ready; fine-tuned checkpoint and robot stream pending**.

The real Ultralytics classification boundary is implemented without enabling
premature species output. It accepts only a checkpoint whose native class names
map one-to-one to the canonical six outputs. Framework tensors, `Results`, and
native class names remain inside the adapter; downstream runtime code receives
only immutable `ClassificationObservation` values.

## Implemented

- Strict mapping for `ragdoll / singapura / persian / sphynx / pallas /
  not_target`, including deterministic stripping of indexed directory prefixes.
- Centred `wide=1.0`, `medium=0.8`, and `tight=0.6` crops with bounds and frame
  metadata checks. This is operator-guided classification, not object detection.
- Lazy load, warmup, inference, health, and close lifecycle compatible with the
  existing `ModelRunner[ClassificationObservation]` protocol.
- Temperature-ready probability adaptation, canonical top-3 and margin, with
  temperature held at the uncalibrated neutral value `1.0`.
- Explicit invalid observations for stale frames, malformed images, mapping
  errors, missing `Results.probs`, and inference exceptions. No old result is
  reused after a failure.

## ImageNet Base-Weight Safety Check

The official `yolo26s-cls.pt` loads successfully but exposes 1,000 ImageNet
classes. The adapter rejected it because a Cat Census checkpoint must expose
exactly six classes. The check emitted no species line and no census event.

This matters because loading the correct architecture is not evidence that the
model has been fine-tuned. Species output will become possible only after Gate
B1 passes and a trained six-class checkpoint is registered.

## Measured RTX 4070 Smoke Latency

Thirty synchronized, warm GPU predictions of the raw base classification model
at 224 pixels produced:

| Metric | Result |
| --- | ---: |
| Mean | 12.76 ms |
| P50 | 14.37 ms |
| P95 | 15.54 ms |
| Mean-derived throughput | 78.38 FPS |

This benchmark excludes capture, ROI scheduling, aggregation, UI, and network
transport. It is raw base-model latency only, not Cat Census accuracy and not
the final end-to-end performance claim.

## Remaining Gates

- B0: real robot frame and stream contract are deferred by the user.
- B1: all 2,321 candidate reviews remain pending.
- B2: requires a registered fine-tuned six-class checkpoint, actual robot
  stream, and visible UI/console integration evidence.

Both Python environments pass all 48 deterministic tests. No split, training,
calibration, robot connection, console species output, census event, or motor
command was produced by this target.
