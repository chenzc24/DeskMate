# DeskMate Deep Learning Demo

This repository contains the Deep Learning and behavior-decision subproject for
a NUS Deep Learning and robotics summer-school demo. The current directory is
the project-structure root, even when it is checked out inside a larger course
workspace. All project plans, logs, rules, code, tests, and documentation are
relative to this directory.

## Current Direction

Work is split into two sequential phases:

```text
Official Baseline (now, due 17 July)
robot stream -> five-breed cat classifier -> visible console/UI -> census
                          |
                          v reuse proven infrastructure
DeskMate Advanced (only after Baseline Gate B4)
multi-expert perception -> WorldState -> FSM -> safety gate -> robot adapter
```

The current P0 is the official Great Cat Census: fine-tune the Ultralytics
`yolo26s-cls.pt` whole-image classifier for Ragdoll, Singapura, Persian, Sphynx,
and Pallas cat plus an internal `not_target` rejection output; run it on
quality-gated, operator-aligned multi-scale ROIs from the live robot camera;
calibrate and aggregate correlated probabilities; print only confirmed target
species; and support the remotely piloted 15-minute course. Baseline does not
train an object detector or implement autonomous search. Model selection,
calibration, and untouched robot final testing use separate data. Advanced work
is paused until the Baseline passes three complete rehearsals and its offline
release is frozen.

Both phases target the local NVIDIA RTX 4070 plus CPU and must remain usable
without cloud inference. Advanced reuses the Baseline's Ultralytics/PyTorch
toolchain, bounded-queue frame capture, reconnect, model packaging, generic
`ModelRunner` lifecycle, UI, telemetry, replay tests, and robot video
configuration. Cat classification
weights, heads, labels, datasets, thresholds, and `Results.probs` are not reused
as detection assets.

## Current Gate Status

Baseline Gate B0 is **NOT PASSED**. The software and data-pilot checks are
complete. The requested camera profile is now 480 x 480 JPEG quality 85 at
8 FPS, upright and not mirrored, with OpenCV BGR output after decode. Two human
inputs remain: one consented frame from the actual robot camera and its delivery
protocol/endpoint. The exact collection steps and ownership blanks are exposed in the
[Phase 0 manual-action dashboard](docs/evaluation/BASELINE_PHASE0_MANUAL_ACTIONS.md).

Gate B1 human image review is now **IN PROGRESS**. The latest machine audit still
has 2,321 pending candidates and zero accepted images until reviewer decisions
are written back. This is a separate dataset-freeze blocker, not a third Gate
B0 failure.

## Entry Documents

- [High-level plan index](docs/plans/README.md): authority order and document
  scope.
- [Official Baseline plan](docs/plans/BASELINE_PLAN.md): five-cat data, model,
  robot-stream integration, three-day schedule, report evidence, and gates.
- [DeskMate Advanced plan](docs/plans/ADVANCED_PLAN.md): post-Baseline
  multi-expert perception, semantic fusion, decisions, safety, and schedule.
- [Advanced dataset sourcing](docs/plans/ADVANCED_DATASET_SOURCING.md):
  post-Baseline desk-object data-source decisions.
- [Advanced dataset download plan](docs/plans/ADVANCED_DATASET_DOWNLOAD_PLAN.md):
  post-Baseline acquisition and local storage workflow.
- [Formal requirement transcriptions](<References/The requirement/>): local
  evidence for the assignment, evaluation SOP, announcement, and answer book.
- [Repository Agent rules](AGENTS.md): model, data, validation, robot-safety,
  and commit policy.
- [Repository workflow](plan/README.md): target plans and factual maintenance
  logs.
- [Phase 0 manual-action dashboard](docs/evaluation/BASELINE_PHASE0_MANUAL_ACTIONS.md):
  open robot evidence for B0 and the separate human image-review queue for B1.

## Development Workflow

From this `/project` root:

1. Run `git status --short --branch` and audit existing dirty files.
2. Create `plan/<YYYY-MM-DD-target-name>/plan.md` from the repository
   template.
3. Declare owned and read-only paths before editing.
4. Implement only the bounded target.
5. Run target-specific validation plus `git diff --check` and
   `git status --short --branch`.
6. Record the factual outcome in `plan/log.md`.
7. Commit or push only when explicitly requested.

## Repository Boundary

This directory is the independent `chenzc24/DeskMate` repository and is tracked
as the `project` Git submodule by the containing course repository. The parent
checkout remains outside this project's workflow boundary. Large datasets,
downloaded model weights, private videos, and training outputs are local
artifacts and must not be committed.
