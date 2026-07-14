# DeskMate Deep Learning Demo

This repository contains the Deep Learning and behavior-decision subproject for
a NUS Deep Learning and robotics summer-school demo. The current directory is
the project-structure root, even when it is checked out inside a larger course
workspace. All project plans, logs, rules, code, tests, and documentation are
relative to this directory.

## Current Direction

The baseline is a local, no-cloud multi-expert perception system:

```text
object expert + face/eye expert + hand expert
    -> timestamped observations
    -> temporal evidence fusion
    -> WorldState
    -> decision FSM
    -> safety gate
    -> robot adapter
```

Training and inference target the local NVIDIA RTX 4070 plus CPU. The demo must
remain usable offline and degrade safely when an expert, camera, or controller
is unavailable.

## Entry Documents

- [Baseline plan](BASELINE_PLAN.md): demo scope, models, architecture, safety,
  schedule, tests, and Definition of Done.
- [Dataset sourcing](DATASET_SOURCING.md): candidate data sources and source
  policy.
- [Dataset download plan](DATASET_DOWNLOAD_PLAN.md): acquisition and local
  storage workflow.
- [Repository Agent rules](AGENTS.md): model, data, validation, robot-safety,
  and commit policy.
- [Repository workflow](plan/README.md): target plans and factual maintenance
  logs.

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

This directory is the management root of the sub-repository. A containing
course checkout, if present, is outside the project workflow boundary. This
adoption does not create a nested `.git` or invent an independent remote; Git
topology can be changed later only when an actual sub-repository remote and
integration policy are supplied. Large datasets, downloaded model weights,
private videos, and training outputs are local artifacts and must not be
committed.
