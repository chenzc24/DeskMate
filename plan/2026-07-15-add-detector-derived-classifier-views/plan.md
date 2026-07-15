# Add Detector-Derived Views To Classifier Training

## Goal

Update the governing Baseline and Phase 0/phase-boundary plan so the fixed
pretrained cat detector serves two distinct roles without detector annotation:

1. offline, derive padded cat crops from human-accepted classification base
   images for `B-M01` training; and
2. online, optionally propose the matching crop type from robot frames while
   retaining the centre-ROI fallback.

The design must improve train/runtime input alignment without counting crops as
new images, leaking derivatives across splits, dropping detector misses, or
allowing detector bias to change the class distribution silently.

## Dirty-State Decision

The worktree contains active robot-video handoff, human-review handoff, and
pretrained-localizer smoke implementation changes. In particular,
`configs/baseline_localizer.toml`, model manifests, localization source/tests,
and localizer smoke reports belong to another target and remain read-only. This
target modifies plans and the factual maintenance log only.

## Owned Files

- `docs/plans/BASELINE_PLAN.md`
- `plan/2026-07-14-baseline-phase-0-foundation/plan.md`
- `plan/2026-07-15-add-detector-derived-classifier-views/plan.md`
- `plan/log.md`

## Read-Only Files And Directories

- `References/The requirement/**`
- `AGENTS.md` and `README.md`
- `configs/**`
- `models/**`
- `src/**`, `scripts/**`, and `tests/**`
- `docs/evaluation/**`
- `docs/plans/ADVANCED_PLAN.md` and Advanced dataset plans
- all other target plans, including the active localizer smoke and review/video
  handoff targets

## Dependencies

- Human-accepted and deduplicated five-breed/`not_target` base images; review is
  currently in progress and Gate B1 is not yet passed.
- A grouped 85% train / 10% `val_select` / 5% `val_cal` split at base-image
  level before any crop is generated.
- Pinned official COCO `B-D01=yolo26s.pt`; the existing smoke result is useful
  feasibility evidence but is not robot-domain admission evidence.
- Local RTX 4070 and the existing ignored data/artifact policy.
- Robot video currently in handoff for later same-video runtime comparison.

## Decisions

- Detector crops are derived views, never unique dataset counts or detector
  labels. Each crop retains a `parent_image_id` and inherits its parent's split.
- Human breed review and deduplication precede split freeze and crop generation.
- A detector miss never removes a target base image; the original/letterboxed
  view remains available and the miss is reported per class.
- For a detected base image, keep one deterministic primary padded crop for
  validation. Training may apply bounded padding jitter, but may not create
  extra statistical weight for that parent.
- The training loader samples by base image and selects exactly one view per
  access: original or detector crop. Initial crop probability is 0.5 and is a
  `val_select` hyperparameter, not a fixed accuracy claim.
- If that loader is not verified before first training, materialize exactly one
  view per parent (valid crop, otherwise original) so the existing folder
  trainer can run without double-weighting hits or delaying the first seed.
- `val_select` and `val_cal` preserve base-image counts and report original,
  frozen detector-crop, and runtime-policy views separately. No derivative may
  cross a split or be counted as another validation image.
- Other-breed cat crops are useful `not_target` views; no-cat backgrounds remain
  original/centre-ROI `not_target` views; reviewed detector false-positive
  crops may become hard negatives.
- The assignment's five example images and all `robot_calibration`/
  `robot_final` media stay out of classifier training and crop-derived training
  artifacts.

## Implementation Scope

This target changes documentation only. A later bounded implementation target
must introduce the derived-view manifest, crop generator, base-balanced loader,
contact-sheet review, deterministic fixtures, and training-config fields
together. It must not modify the active localizer smoke artifacts implicitly.

## Deterministic Validation

- Check split-before-derive order, `parent_image_id` inheritance, derivative
  count exclusion, and no assignment/robot-test contamination.
- Require fixtures for detector hit/miss/multi-box, padding/clamping, per-class
  coverage, deterministic validation crops, base-balanced sampling, original
  fallback, and `not_target` routing.
- Confirm official 85/15 reporting remains based on unique base images.
- Check model IDs, Gate/phase ownership, current handoff status, local links,
  Markdown fences/whitespace, `git diff --check`, and final status scope.

## Recorded-Video Validation

When the robot video is accepted, evaluate the classifier on the same frozen
clips with original/centre input, detector crop, and detector-plus-fallback
policy. Report per-class detector coverage, classifier metrics by view,
time-to-confirm, FPS, and P95. This plan change claims none of those results.

## Real Robot Motion

None. Offline crop derivation and replay evaluation do not control the robot.

## Commit Intent

Do not stage, commit, push, or open a pull request. Preserve all existing dirty
implementation work and leave this plan update for human review.

## Validation Results

- Confirmed `References/The requirement/**` is unchanged and official counts/
  85/15 reporting remain based on unique five-breed base images.
- Confirmed the Baseline v1.4 order is human review/dedup, grouped split,
  detector-derived views, base-balanced training, and later robot replay; no
  crop can cross a split or become a new official image.
- Confirmed detector miss/invalid retains the original parent, per-class
  coverage is required, other-breed/no-cat/hard-negative `not_target` routes
  are distinct, and assignment/robot calibration/final media are excluded.
- Confirmed the tested multi-view path has a bounded one-view-per-parent folder
  fallback so custom-loader work cannot block the first training seed or
  double-weight detector hits.
- Cross-checked the current localizer smoke report: official `B-D01` resolved
  native `cat`, produced proposals on all five assignment smoke images, and
  remains disabled/not release-admitted; those images remain training-excluded.
- Resolved all 7 local links; parsed the illustrative YAML with a real parser;
  checked semantic guards, required terms, trailing whitespace, balanced code
  fences, requirement immutability, and `git diff --check` successfully.
- Reviewed project-root status. Existing localizer/video/review implementation
  changes remained read-only; this target downloaded no asset, generated no
  crop, trained no model, moved no robot, and staged/committed/pushed nothing.
