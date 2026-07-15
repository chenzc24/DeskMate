# Execute Baseline Phase 0 And Gate B0

## Goal

Implement and validate the executable Baseline Phase 0 foundation defined by
`docs/plans/BASELINE_PLAN.md`: six-output data contracts and source-pilot
tooling, a bounded robot-frame/runtime skeleton, deterministic fixtures, and a
machine-readable Gate B0 report. This target does not perform bulk acquisition,
model training, calibration, final robot evaluation, or physical motion.

## Dirty-State Note

Start state from `git status --short --branch`:

```text
## main...origin/main
 M AGENTS.md
 D BASELINE_PLAN.md
 D DATASET_DOWNLOAD_PLAN.md
 D DATASET_SOURCING.md
 M README.md
 M plan/log.md
?? docs/plans/
?? plan/2026-07-14-baseline-phase-0-foundation/
?? plan/2026-07-14-harden-baseline-architecture/
?? plan/2026-07-14-organize-high-level-plans/
?? plan/2026-07-14-revise-baseline-yolo-classification/
?? plan/2026-07-14-split-baseline-advanced-plans/
```

These are the intentional uncommitted plan reorganization and hardening changes.
They define contracts for this target but remain read-only except for the shared
maintenance log. No existing change will be discarded, staged, or rewritten.

## Owner

- Target owner: `Codex / Baseline Phase 0 implementation`

## Owned Files

- `pyproject.toml`
- `src/deskmate_baseline/**`
- `tests/**`
- `configs/baseline_phase0.toml`
- `configs/baseline_sources.toml`
- `configs/phase0_pilot_review.toml`
- `data/README.md`
- `data/manifests/source_manifest.template.csv`
- `scripts/data/audit_source_manifest.py`
- `scripts/data/build_pilot_contact_sheets.py`
- `scripts/data/run_source_pilot.py`
- `scripts/runtime/run_phase0_skeleton.py`
- `scripts/tools/verify_gate_b0.py`
- `data/downloads/phase0_pilot/**` — ignored generated pilot images/metadata;
  never stage or commit
- `docs/evaluation/BASELINE_PHASE0_B0_REPORT.md`
- `docs/evaluation/BASELINE_PHASE0_B0_REPORT.json`
- `plan/log.md`
- This target plan

## Read-Only Files And Dirty Paths

- `References/The requirement/**`
- `docs/plans/**`
- `AGENTS.md` and `README.md`
- All earlier target plans
- `scripts/data/download_dataset_sources.ps1`
- Existing user browser/Chrome preparation
- Any parent-workspace paths and all non-pilot raw dataset/model artifact paths

## Shared Dependencies

- Python 3.13.1 is currently available.
- `pytest`, `numpy`, PyYAML, and Pydantic are installed; OpenCV, Selenium,
  PyTorch, Torchvision, and Ultralytics are not currently installed.
- Phase 0 core code will use the Python standard library so contract tests do
  not depend on the future training environment. Optional NumPy arrays may be
  carried as opaque frame payloads.
- The local GPU is an NVIDIA GeForce RTX 4070 Laptop GPU with 8,188 MiB reported
  VRAM. Phase 0 makes no GPU-performance claim.
- A real robot stream URL/protocol and recorded robot frame are external
  dependencies that must be supplied or discovered before the real-stream B0
  item can pass. Assignment example images may be used only for smoke tests and
  never as training data.

## Expected Work

1. Define canonical labels, `FramePacket`, `ClassificationObservation`, model
   runner protocol, quality result, and confirmation/console event contracts.
2. Implement bounded latest-frame, single-pending-preview, prioritized
   confirmation, stale-frame invalidation, and deterministic aggregation
   skeletons without framework-native result leakage.
3. Add a manifest template and auditor for provenance, licensing, label order,
   exact/perceptual hashes, source/session groups, review state, split state,
   class coverage, and Selenium go/no-go calculation.
4. Add a configuration file that records Phase 0 thresholds as provisional and
   keeps calibration/final thresholds explicitly unfrozen.
5. Add deterministic tests for six-output order, invalid observations,
   `not_target`, preview-without-console, exactly-once confirmation output,
   stale-frame clearing, bounded queue/drop behavior, and manifest validation.
6. Run the skeleton with an approved local smoke-test image and, if available,
   a recorded/live robot frame. Do not treat the five assignment examples as
   dataset inventory.
7. Produce a Gate B0 report that distinguishes passed deterministic evidence,
   missing external robot evidence, and Phase 1 work. Never claim B0 passed if
   required real-frame or source-pilot evidence is missing.

## Deterministic Validation

- `python -m compileall -q src tests scripts`
- `python -m pytest -q tests`
- Run the manifest auditor on a valid small fixture and on invalid label,
  duplicate, missing-license, and cross-split duplicate fixtures.
- Run the skeleton fixture and verify preview emits no species line,
  confirmation emits one canonical line, stale input clears state, and queue
  counters are bounded.

## Recorded-Video Validation

- Prefer a robot-team supplied recorded frame/video or configured live stream.
- Record source type, dimensions, color/orientation handling, frame timestamp,
  stale behavior, and output event in the B0 report.
- If only an assignment example is available, mark the software smoke test pass
  but the real robot-frame B0 evidence incomplete.

## Real Robot Motion

None. The Baseline DL process sends no motor command. Any live-stream check is
read-only and must not control the chassis.

## Commit Intent

No automatic branch, commit, push, or PR. Leave the bounded Phase 0
implementation and evidence for user review.

## Validation Results

Implemented the bounded Phase 0 foundation without enabling model training,
Selenium, dataset bulk download, or robot motion.

- Added canonical six-output contracts, a framework-neutral model-runner
  boundary, bounded capture/inference queues, quality gating, temporal state,
  exactly-once confirmation presentation, and stale-state invalidation.
- Added source-pilot acquisition, manifest generation/auditing, contact-sheet
  review support, a runtime smoke script, and a fail-closed Gate B0 verifier.
- Downloaded 60 pilot candidates into the ignored quarantine area: 10 each for
  Commons Ragdoll, Singapura, Persian, Sphynx, and Pallas, plus 10 iNaturalist
  Pallas candidates. All remain `quarantine`; accepted counts remain zero.
- The final manifest audit reported 60 rows, zero schema/provenance errors, and
  zero warnings. The single-review visual triage is explicitly non-authoritative.
- `python -m compileall -q src tests scripts` passed.
- `python -m pytest -q tests` passed with 19 tests.
- The assignment-image runtime smoke passed queue priority, preview silence,
  exactly-once confirmation, and stale-state clearing. It is marked
  `assignment_smoke` and is not robot-camera or dataset evidence.
- JSON/TOML parsing and `git diff --check` passed after the implementation.

Gate B0 was audited and correctly returned `NOT_PASSED` (verifier exit code 3).
Eight of twelve checks passed. The four open evidence items are:

1. a bounded Oxford-IIIT Pet image pilot for the three covered target breeds;
2. a representative `not_target` source pilot, including robot-background
   negatives;
3. one consented recorded or live frame from the actual robot camera;
4. the robot stream protocol, endpoint/configuration method, orientation,
   resolution/FPS behavior, and color format.

Machine-readable and human-readable evidence is stored under
`docs/evaluation/BASELINE_PHASE0_B0_REPORT.*`. No branch, commit, push, or PR was
created for this target.
