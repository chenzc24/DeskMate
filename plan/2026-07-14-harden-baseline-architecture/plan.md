# Harden Baseline Architecture And Model Selection

## Goal

Apply the architecture review to the durable Baseline and Advanced principles:

- reject non-target scenes instead of forcing every frame into one cat breed;
- separate robot-domain calibration from untouched final evaluation;
- calibrate probabilities and replace correlated majority voting with
  quality-gated probability aggregation;
- prevent confirmation bursts from blocking capture or UI;
- reuse generic model lifecycle infrastructure while retaining task-specific
  classification and detection outputs; and
- make Advanced YOLO fine-tuning and model size evidence-gated.

## Dirty-State Note

The worktree contains the uncommitted high-level-plan restructuring and model
revision targets, all intentionally in scope. The separate untracked
`plan/2026-07-14-baseline-phase-0-foundation/` target is existing work and
remains read-only.

## Owned Files

- `docs/plans/BASELINE_PLAN.md`
- `docs/plans/ADVANCED_PLAN.md`
- `AGENTS.md`
- `README.md`
- `plan/log.md`
- This target plan.

## Read-Only Files

- `References/The requirement/**`
- `docs/plans/ADVANCED_DATASET_*.md`
- `plan/2026-07-14-baseline-phase-0-foundation/**`
- All other prior target plans, scripts, and experience notes.

## Decisions

- Baseline has five target labels plus an internal `not_target` rejection class.
- Preserve the official 85/15 target-cat split; add 300–600 grouped negative
  images without reporting them as target-cat counts.
- Add a robot calibration set of 25 unseen target images plus negative scenes;
  preserve 50 unseen target images and a negative-scene set for final testing.
- Fit temperature and per-class confidence/margin thresholds only on calibration
  data; report ECE and never tune on final test.
- Use blur/exposure/freshness/ROI quality gates and aggregate calibrated
  probabilities across correlated scales/frames instead of calling them 15
  independent votes.
- Separate latest-frame capture, preview, confirmation, and presentation workers.
- Share `ModelRunner[OutputT]` lifecycle; use `ClassificationObservation` for
  Baseline and `ExpertObservation` for Advanced.
- Integrate YOLO26s-cls first; benchmark YOLO26m-cls only after the live path
  works. Keep EfficientNet-B0 evidence-gated.
- In Advanced, benchmark pretrained YOLO26n before fine-tuning and compare
  YOLO26s only when recall is insufficient and total P95 budget allows it.

## Validation

- Confirm all formal requirements remain represented and requirement files are
  unchanged.
- Confirm active documents consistently name the six internal outputs, five
  reportable target breeds, calibration/final separation, ECE, generic runner,
  and task-specific result schemas.
- Confirm obsolete `10/15` voting, automatic navigation-time console output,
  mandatory M01 fine-tuning, and fixed Advanced `n` choice are removed.
- Resolve active Markdown links and run whitespace, code-fence,
  `git diff --check`, and final status-scope checks.

## Deterministic And Recorded-Video Validation

This is documentation-only. The plan must define deterministic fixture tests and
recorded robot-video gates, but this target does not claim those runtime results.

## Real Robot Motion

None.

## Commit Intent

Do not commit or push automatically; leave the combined plan changes for human
review.

## Validation Results

- Confirmed `References/The requirement/**` is unchanged and re-checked the
  formal five-species, 85/15 split, live-feed, console/UI, eight-image,
  remote-control, no-autonomous-control, CNN/YOLO, and over-1,000-image terms.
- Confirmed the active principles consistently contain the five reportable
  labels plus internal `not_target`, `val_select`/`val_cal`, separate
  `robot_calibration`/`robot_final`, temperature/ECE, `ModelRunner`, and the
  classification/detection observation boundary.
- Confirmed obsolete `10/15` voting, navigation-time automatic console output,
  mandatory Advanced M01 fine-tuning, and `InferenceBackend` boundary wording
  are absent.
- Resolved 20 active local Markdown links; all targets exist.
- Checked all active files for trailing whitespace and balanced code fences;
  ran `git diff --check` successfully.
- Reviewed final status from the project root. Existing uncommitted plan moves
  and earlier target directories remain present; no file was staged, committed,
  or pushed by this target.
