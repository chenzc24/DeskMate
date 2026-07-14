# DeskMate Repository Rules

This directory is the structural root of the DeskMate sub-repository. These
rules apply to every path below it and incorporate the plan-log-experience
workflow from
[`chenzc24/agent-workflow-kernel`](https://github.com/chenzc24/agent-workflow-kernel).

## Project Scope

This repository contains the NUS Deep Learning and robotics demo. Treat the
current directory as `/project`: all project plans, logs, experience notes,
configuration, source code, tests, data manifests, and entry documentation are
managed relative to this root. The containing course workspace is outside the
project's ownership unless a correction target explicitly names a parent path.

Primary entry documents:

- `README.md`: stable repository entry point;
- `BASELINE_PLAN.md`: product scope, architecture, model IDs, safety,
  schedule, and acceptance gates;
- `DATASET_SOURCING.md`: dataset source decisions;
- `DATASET_DOWNLOAD_PLAN.md`: dataset acquisition plan;
- `plan/README.md`: target planning and maintenance-log protocol.

When these documents disagree, stop and resolve the contract in a bounded
target before implementing dependent code.

## Target Workflow

Before editing repository files, create or update:

```text
plan/<YYYY-MM-DD-target-name>/plan.md
```

Each target must name:

- the concrete demo or engineering outcome;
- exact owned files/directories;
- existing dirty paths left read-only;
- model, dataset, hardware, or protocol dependencies;
- deterministic validation and recorded-video validation;
- whether real robot motion is involved;
- commit intent or an explicit no-commit policy.

Do not combine data acquisition, model changes, fusion-policy changes, robot
protocol changes, and presentation-only work in one target unless the plan
explains why they are inseparable.

## Architecture Contracts

Treat `BASELINE_PLAN.md` as the current architecture source of truth.

- `M01`: global object expert (`yolo26n.pt`, with documented fallback);
- `M02`: MediaPipe Face Landmarker;
- `M03`: MediaPipe Gesture Recognizer;
- `C01`: ByteTrack tracking component;
- `M04` and `M05`: optional P1 components, not P0 dependencies.

All perception backends must emit the canonical `ExpertObservation` contract.
Framework-native tensors or result objects must not cross into the semantics
layer. The fusion layer must align observations by Track ID and timestamp,
respect quality and TTL, and represent missing values as `unknown`, not zero.

The control dependency is one-way:

```text
camera -> experts -> observations -> WorldState -> semantic events -> FSM -> safety gate -> robot adapter
```

Experts never issue motor commands. The FSM never bypasses the safety gate.
Any schema or robot-command change is a shared-contract change and requires a
target plan, producer/consumer updates, and contract tests in the same target.

## Model And Dataset Policy

- Prefer official or institution-maintained model sources with complete model
  cards. Record source URL, pinned version, SHA-256, license, input/output, and
  enabled priority in `models/manifest.yaml` when that file is introduced.
- Downloaded weights, raw datasets, extracted frames, private videos, training
  runs, and large generated artifacts stay out of Git. Commit manifests,
  scripts, schemas, small fixtures, and reproducible configuration instead.
- Never commit secrets, access tokens, signed dataset URLs, or personal identity
  data.
- Split video-derived data by recording session, not random adjacent frames.
- Do not perform face identification. Face signals are limited to landmarks,
  quality, head/eye motion, and task-relevant temporal events.
- Validate every pretrained model on the actual robot camera view before
  deciding whether to fine-tune it.
- Do not add a model merely to increase model count. A new expert must supply an
  independently useful signal and pass an ablation or failure-case comparison.
- Do not replace a pinned model or threshold without recording before/after
  metrics on the same held-out videos.
- The final demo must load all required assets without internet access.

## Validation By Change Type

Every target runs `git diff --check` and `git status --short --branch` from this
project root, plus the applicable checks below. If Git currently resolves to a
containing checkout, scope diff and status review to project-owned paths and
record unrelated parent dirty state in the target plan.

### Documentation Or Configuration

- Confirm referenced local paths exist or are explicitly marked future work.
- Parse JSON/YAML examples with a real parser when practical.
- Check that model IDs, schema fields, priorities, and Gate definitions remain
  consistent across changed documents.

### Python Code

- Run targeted unit tests for the changed module.
- Run `python -m pytest -q tests` when the test suite exists.
- If no test suite exists yet, run import/compile checks and a small deterministic
  fixture; record the limitation in the target plan and log.
- Do not claim GPU or real-time performance from code inspection alone.

### Perception Or Fusion

- Test on held-out recorded video from the actual camera viewpoint.
- Report per-expert validity rate, missing/stale rate, latency, and relevant task
  metrics.
- Report end-to-end throughput and P95 latency with all enabled P0 experts.
- Exercise stale output, missing expert, wrong Track ID, and low-quality ROI
  cases.
- Compare behavior-event output on the same videos before and after changes.

### Robot Integration

- Pass Mock Adapter and protocol tests before enabling physical motion.
- Verify command TTL, watchdog, `STOP` priority, disconnect behavior, and manual
  emergency stop.
- Do not enable autonomous forward motion without independent distance or
  collision protection.
- Real-motion tests require an operator, a clear test area, low initial speed,
  and an immediately available emergency stop.

## Artifact And Logging Rules

- Runtime logs belong under ignored/generated artifact paths, not source
  directories.
- Evaluation summaries committed to Git must identify dataset/video version,
  configuration, model checksums, and hardware.
- UI screenshots and demo videos are evidence artifacts; do not use them as the
  only correctness gate.
- Update `plan/log.md` with factual results after validation. Do not create an
  experience note unless a human requests one.

## Commit And Branch Policy

- Do not automatically create a branch, commit, push, or PR unless the user
  explicitly requests it.
- When a new branch is requested, use the repository's configured branch prefix
  unless the user specifies another name.
- Keep one bounded target per commit and stage only the files named in its plan.
- Never stage unrelated dirty paths from the containing course workspace.
