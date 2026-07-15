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
- `docs/plans/README.md`: high-level plan index and authority order;
- `docs/plans/BASELINE_PLAN.md`: official five-breed Cat Census principles,
  due 17 July 2026;
- `docs/plans/ADVANCED_PLAN.md`: post-Baseline DeskMate design principles and
  acceptance gates;
- `docs/plans/ADVANCED_DATASET_SOURCING.md`: post-Baseline desk-object data
  principles;
- `docs/plans/ADVANCED_DATASET_DOWNLOAD_PLAN.md`: post-Baseline acquisition
  principles;
- `References/The requirement/`: read-only authoritative originals and faithful
  local transcriptions of the assignment, SOP, announcement, and answer book;
- `plan/README.md`: target planning and maintenance-log protocol.

The materials under `References/The requirement/` outrank project-authored
plans. The documents under `docs/plans/` express durable design and delivery
principles; a dated target plan defines the bounded implementation work. When
these documents disagree, stop and resolve the contract in a bounded target
before implementing dependent code.

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

Architecture authority is phase-specific:

- Until official Baseline Gate B4 passes,
  `docs/plans/BASELINE_PLAN.md` is the only P0 project principle.
  `References/The requirement/` overrides it if the two ever disagree.
- After the Baseline release is frozen, `docs/plans/ADVANCED_PLAN.md` becomes
  the governing project principle for DeskMate Advanced. Advanced work must not
  consume Baseline-critical integration time before that gate.

The official Baseline uses one active classifier with five reportable breeds and
one internal rejection output:

- `B-M01`: Ultralytics `yolo26s-cls.pt`, ImageNet-pretrained, using the
  **classification** task and `Results.probs`, not object detection;
- `B-M01F`: Torchvision EfficientNet-B0 is an evidence-gated backup after the
  primary live pipeline works, not a second P0 dependency;
- canonical target label order:
  `ragdoll / singapura / persian / sphynx / pallas`, followed internally by
  `not_target`, which is never printed as a cat species;
- reusable lifecycle boundary:
  `FramePacket -> ModelRunner[ClassificationObservation]`; Advanced keeps
  `ModelRunner` but emits `ExpertObservation` from detection backends;
- operator-guided multi-scale centre ROIs plus temporal consensus replace any
  assumption of autonomous search or alignment;
- blur, exposure, freshness, and ROI-coverage gates must pass before a frame can
  contribute to confirmation;
- capture, preview, confirmation, and presentation use bounded queues so a
  confirmation burst cannot block video display or remote driving;
- remote driving stays outside the DL process; Baseline DL code never issues
  motor commands.

Framework-native tensors or result objects must not cross from `B-M01` into UI,
logging, or integration code. Raw `Results.probs` must be adapted, temperature
calibrated, and aggregated as correlated spatial/temporal evidence rather than
counted as independent votes. The live UI must visibly show each confirmed
species, print only confirmed target species to the console, and invalidate
temporal state after stale or missing frames.

Baseline data targets 2,000 clean unique images (400 per class), may stretch to
3,000 without delaying integration, and must never release below 1,200. The
internal `not_target` class adds 300–600 source/session-grouped negatives. Keep
the target-cat split at 85% train, 10% model selection, and 5% calibration so
the latter two still total the required 15% validation. Robot-domain calibration
uses 25 unseen target base images plus negative scenes; the final gate uses a
separate 50 target images and 50 negative scenes exactly once. Repeated camera
frames do not increase those counts.

DeskMate Advanced extends the proven Baseline capture, model packaging, replay,
telemetry, and UI infrastructure with:

- `M01`: global object expert; benchmark pretrained `yolo26n.pt` first, compare
  `yolo26s.pt` only when recall is insufficient and the full-expert P95 budget
  permits it, and fine-tune only after real-camera evidence justifies it;
- `M02`: MediaPipe Face Landmarker;
- `M03`: MediaPipe Gesture Recognizer;
- `C01`: ByteTrack tracking component;
- `M04` and `M05`: optional P1 components, not Advanced P0 dependencies.

Advanced perception backends emit the canonical `ExpertObservation` contract.
The fusion layer aligns observations by Track ID and timestamp, respects quality
and TTL, and represents missing values as `unknown`, not zero. Its control
dependency remains one-way:

```text
camera -> experts -> observations -> WorldState -> semantic events -> FSM -> safety gate -> robot adapter
```

Experts never issue motor commands. The FSM never bypasses the safety gate. Any
shared schema or robot-command change requires a target plan, producer/consumer
updates, and contract tests in the same target.

## Model And Dataset Policy

- Prefer official or institution-maintained model sources with complete model
  cards. Record source URL, pinned version, SHA-256, license, input/output, and
  enabled priority in `models/manifest.yaml` when that file is introduced.
- Downloaded weights, raw datasets, extracted frames, private videos, training
  runs, and large generated artifacts stay out of Git. Commit manifests,
  scripts, schemas, small fixtures, and reproducible configuration instead.
- Never commit secrets, access tokens, signed dataset URLs, or personal identity
  data.
- For the official Baseline, keep the required 85% train / 15% validation ratio,
  stratify by the five cat breeds, and keep duplicate/near-duplicate source
  groups in one split. Do not train on the five assignment example images.
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
