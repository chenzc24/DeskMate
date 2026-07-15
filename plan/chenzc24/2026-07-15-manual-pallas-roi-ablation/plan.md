# Manual Pallas ROI Ablation

## Outcome

Determine whether the two robot-camera Pallas failures are caused primarily by
detector/localizer crops or by the current `B-M01` classifier. Bypass `B-D01`
with human-drawn cat boxes and compare the unchanged classifier on the original
routed ROI, a tight manual cat box, and a padded manual cat box.

## Owned Paths

- `plan/chenzc24/2026-07-15-manual-pallas-roi-ablation/plan.md`
- `data/downloads/pallas_manual_roi_ablation/` (ignored/generated evidence)
- `plan/log.md` (append-only after validation)

## Read-Only Inputs

- `data/downloads/Camera/微信图片_20260715123701_1251_79.png`
- `data/downloads/Camera/微信图片_20260715123702_1252_79.png`
- `artifacts/robot_camera_eval/batch_20260715_1237/`
- `runs/baseline_provisional/b-m01-provisional-bd01-oneview-seed-20260715/weights/best.pt`
- `runs/baseline_classifier_hardening/soups/b50_p50.pt`
- all other pre-existing dirty and untracked paths

## Dependencies And Protocol

- Python `.venv`, OpenCV, Ultralytics 8.4.95, RTX 4070 Laptop GPU
- canonical label order through `canonical_index_mapping`
- record manual coordinates in source-image pixels and save crops plus an
  annotated comparison sheet
- primary causal test uses the unchanged current classifier; the disabled
  hardened candidate is secondary context only

## Validation

- decode both 640x480 source images
- verify every manual box is in bounds and visually contains the Pallas cat
- hash and load both checkpoints; validate canonical class mapping
- record top-3 probabilities for routed, tight, and padded inputs
- `git diff --check` and scoped `git status --short --branch`
- results are two descriptive still-image diagnostics, not release accuracy

## Robot Motion

No robot connection, command, or physical motion.

## Commit Intent

No commit or push. Generated images and detailed results remain ignored.

## Validation Result

- Both source images decoded as 640x480. Visual inspection confirmed that the
  green tight boxes contain the cat and the yellow padded boxes add contextual
  image area without including the printed breed name.
- Frame 8 current-model results: existing detector crop `persian` 0.8142;
  manual tight `sphynx` 0.5079; manual padded `persian` 0.5832.
- Frame 9 current-model results: existing centre fallback `persian` 0.4592;
  manual tight `persian` 0.7818; manual padded `persian` 0.7834.
- Therefore the current classifier produced zero Pallas predictions across all
  four manual ROIs. Frame 8 also proves that a visually valid tight detector
  crop can still be misclassified.
- Secondary context: the disabled hardened candidate classified both existing
  routed inputs and both padded manual inputs as Pallas, but classified both
  overly tight manual inputs as Persian. Padding/context sensitivity remains a
  real issue, but manual localization alone does not repair current `B-M01`.
- Both checkpoint hashes and canonical mappings passed. Generated JSON/CSV
  parsed, all boxes were in bounds, visual comparison passed, and
  `git diff --check` plus scoped status review passed.
- This remains a two-still causal diagnostic, not a release accuracy claim.
