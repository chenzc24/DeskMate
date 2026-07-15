# Smoke Pretrained Cat Localizer During B1 Review

## Outcome

Use the human-review wait window for a bounded, offline smoke test of the
official COCO-pretrained `B-D01=yolo26s.pt` detector. Add a typed detector
adapter and padded-crop router without enabling the detector in the live
Baseline or changing Gate B0/B1.

This target also resolves the timing contract in the governing Baseline plan:
offline acquisition, adapter tests, and assignment-example smoke may run while
B1 review proceeds; live integration and release admission still wait for the
centre-ROI classifier path and same robot-video evidence.

## Dirty-State Note

The worktree already contains active robot-JPEG configuration, Baseline-plan,
Phase 0, and review-handoff changes. This target owns only the paths below and
will preserve all other dirty content. It appends to the existing plan log and
makes a bounded timing clarification to the already-updated Baseline plan.

Existing paths left read-only include:

- `README.md`, `configs/baseline_phase0.toml`, and `docs/evaluation/BASELINE_PHASE0_*`;
- `docs/evaluation/BASELINE_VIDEO_SOURCE_READINESS.*`;
- `plan/2026-07-14-baseline-phase-0-foundation/`;
- `plan/2026-07-15-activate-robot-jpeg-defaults/`;
- `plan/2026-07-15-add-pretrained-cat-localizer/`;
- `plan/2026-07-15-build-minimal-review-handoff/`;
- `scripts/data/build_phase1_review_handoff.py` and `tests/test_review_handoff.py`;
- all ignored review decisions, candidate data, and robot media.

## Owned Files

- `docs/plans/BASELINE_PLAN.md` (timing clarification only)
- `configs/baseline_localizer.toml`
- `models/manifest.yaml`
- `models/README.md`
- `src/deskmate_baseline/localization.py`
- `scripts/evaluation/verify_pretrained_cat_localizer.py`
- `tests/test_localization.py`
- `docs/evaluation/BASELINE_LOCALIZER_SMOKE.json`
- `docs/evaluation/BASELINE_LOCALIZER_SMOKE.md`
- `plan/2026-07-15-smoke-pretrained-cat-localizer/plan.md`
- `plan/log.md` (append-only)

The downloaded `models/yolo26s.pt` weight is ignored and must not enter Git.

## Dependencies

- Official Ultralytics YOLO26 detect weight from the `v8.4.0` assets release.
- Existing pinned Python 3.12 / PyTorch / Ultralytics CUDA environment.
- Local NVIDIA RTX 4070.
- Five assignment example images as smoke-only inputs; they remain excluded
  from training and are not accuracy evidence.
- Real robot JPG/video is unavailable, so release admission is impossible in
  this target.

## Structure Decision

Do not reorganize the Phase 0 package. Extend it additively with one
task-specific localizer module and config. Preserve `FramePacket`, generic
`ModelRunner[OutputT]`, the active `ClassificationObservation`, and centre-ROI
fallback. The localizer observation contains boxes only and can never report a
breed or emit a census event.

## Deterministic Validation

- Resolve the `cat` class ID from the loaded model's names instead of hardcoding
  it.
- Test valid, missing, stale, malformed, and multiple-box outputs.
- Test confidence/area filtering, box sorting, padding/clamping, and centre-ROI
  fallback.
- Confirm no framework-native tensor/result crosses the adapter.
- Run targeted tests and `python -m pytest -q tests` in both Python environments.
- Parse TOML/YAML/JSON with real parsers when available.
- Verify weight size, SHA-256, task, names, and GPU loading.
- Run the five assignment examples and report only smoke detection/latency.
- Confirm B0 and B1 outcomes are unchanged.
- Run `git diff --check` and scoped status review.

## Recorded-Video Validation

Deferred. The detector stays disabled until the same handed-over robot videos
compare centre ROI, detector crop, and detector-plus-fallback using stable-box
success, false proposals, stale/missing rate, time-to-confirm, FPS, and P95.

## Robot Motion

No robot connection or motion is involved. This component has no motor-command
dependency.

## Commit Intent

No commit, push, branch, or PR was requested.

## Validation Results

- Downloaded the ignored official `yolo26s.pt` asset: 20,422,725 bytes,
  SHA-256 `646f8bc3fe0a656803d95c294f7852321748cb29d13466a1af8862e2db384a1b`.
- The pinned Python 3.12 CUDA environment loaded the model on the RTX 4070 and
  resolved native `cat` class ID 15 from model names.
- All five assignment smoke images produced a cat proposal. After one
  per-image warm-up, 25 detector predictions measured 37.71 ms mean and
  44.52 ms P95. This excludes the live pipeline and is not admission evidence.
- Six targeted localizer/router tests passed. Both Python environments passed
  all 67 currently discovered tests and compile checks.
- TOML, YAML, and JSON parsed and matched weight identity, disabled/admission
  state, and checksums.
- B0 remained `NOT_PASSED` only on `real_robot_frame` and
  `robot_stream_contract`; B1 remained fail-closed with 2,321 pending, zero
  accepted, and zero audit errors.
