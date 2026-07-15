# Freeze Detector-View Training Handoff

## Goal

Implement the Baseline v1.4 offline `B-D01 -> B-M01` data path, freeze exactly
one classifier view per parent, commit the training code directly to Git, and
produce one dataset archive for independent comparison runs.

## Dirty-State Note

The worktree contains the provisional base split and an interrupted
original-view provisional training target. The interrupted run completed one
epoch and part of epoch two before the user redirected the work; its checkpoints
are ignored and must not enter the handoff. This target owns the detector-view
and packaging changes below and leaves official Gate B1 unchanged.

## Owner

- Target owner: `Codex`
- Handoff consumers: user and teammate training independently

## Owned Files

- `configs/baseline_derived_views.toml`
- `configs/baseline_training_provisional.toml`
- `scripts/data/derive_detector_classifier_views.py`
- `scripts/training/train_provisional_baseline.py`
- `scripts/tools/freeze_baseline_training_handoff.py`
- `scripts/tools/fetch_baseline_model_assets.py`
- `scripts/tools/bootstrap_training_env.ps1`
- `tests/test_derived_classifier_views.py`
- `tests/test_provisional_training.py`
- `tests/test_training_handoff.py`
- `tests/test_fetch_baseline_model_assets.py`
- `docs/evaluation/BASELINE_DERIVED_VIEWS.json`
- `docs/evaluation/BASELINE_DERIVED_VIEWS.md`
- `data/downloads/baseline_detector_views/` (ignored/generated)
- `data/downloads/baseline_training_handoff_20260715/` (ignored/generated)
- `plan/2026-07-15-freeze-detector-view-training-handoff/plan.md`
- `plan/log.md` (append only)

## Read-Only Files

- base-image source, intake, provisional split, and manifests
- `models/yolo26s.pt`, `models/yolo26s-cls.pt`, and `models/manifest.yaml`
- existing localizer implementation/config/smoke evidence
- interrupted `runs/baseline_provisional/b-m01-provisional-seed-20260715/`
- official Gate B1, robot, requirement, Advanced, and presentation paths

## Shared Dependencies

- `B-D01=yolo26s.pt` remains frozen COCO-pretrained detection; it is never
  fine-tuned and never predicts breed.
- Every derived view inherits `parent_image_id`, canonical label, and split.
- Target cats use one deterministic padded primary crop on hit and original on
  miss/invalid.
- Known other-breed-cat negatives may use a cat crop; other negative backgrounds
  retain original views unless false-positive crops are separately reviewed.
- Exactly one selected file per parent is materialized for the standard
  Ultralytics classification loader.
- Assignment/robot calibration/final media remain excluded.

## Expected Work

1. Generate a complete `view_manifest.csv` with original and optional crop
   rows, detector identity, box/confidence/padding/status, parent, and split.
2. Materialize one selected view per parent into six-class train/val/val-cal
   directories and report per-class detector coverage.
3. Retarget the provisional training guard/config to the one-view dataset.
4. Freeze a dataset-only archive with deterministic inventory and SHA-256;
   deliver code through Git and fetch the pinned classifier base weight from its
   manifest URL during environment bootstrap.
5. Exclude all interrupted run checkpoints and all nonessential local data.

## Validation

- Targeted derived-view, training-guard, and handoff tests.
- Both Python environments' complete suites.
- Real RTX 4070 derivation with pinned B-D01 and full materialized integrity
  verification.
- Exactly 2,787 selected files and one selected view per parent; zero split or
  label inheritance errors.
- Dry-run fine-tune command succeeds from a clean extracted handoff root.
- Archive inventories and SHA-256 verification pass after extraction.
- Official B1 remains fail-closed; requirements remain unchanged.
- `git diff --check` and scoped status review.

Recorded-video validation is not applicable to offline training-view creation.

## Robot Motion

No robot connection or motion is involved.

## Experience Signal (for human review)

The original-only training attempt showed why the handoff contract must be
frozen before parallel runs. Parallel training is meaningful only when both
people share identical parent split, derived-view policy, code, weights, and
checksums.

## Commit Intent

Commit the bounded code/configuration/evidence changes and push directly to the
current `main` branch as explicitly requested. Do not create a PR.

## Outcome

- Generated 4,745 auditable view rows from 2,787 frozen parents and selected
  exactly one view per parent: 1,958 detector crops and 829 originals/fallbacks.
- Preserved every parent label and split; materialized train/val/val-cal counts
  exactly match the provisional base split.
- Frozen one deterministic dataset-only ZIP. Its SHA-256 is recorded in
  `docs/evaluation/BASELINE_DERIVED_VIEWS.json`; code is frozen by Git.
- Extracted the dataset into a clean repository-shaped directory, verified all
  2,789 inventory entries, confirmed 2,787 training images and zero interrupted
  checkpoints, and passed the repository training dry-run.
- Official Gate B1 remains false. This is a development-only parallel-training
  handoff, not a final Baseline release.
