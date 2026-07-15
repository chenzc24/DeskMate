# Validation-Only Full Pipeline Review

## Outcome

Evaluate the unchanged `B-D01 -> crop/fallback -> B-M01` chain on every frozen
`val_select` and `val_cal` parent, excluding all `train` parents.

## Owned Paths

- `plan/chenzc24/2026-07-15-validation-only-full-pipeline/plan.md`
- `data/downloads/baseline_full_pipeline_validation_only/` (ignored/generated)
- `plan/log.md` (append only)

## Existing Dirty Paths Left Read-Only

- `.gitignore`, all existing evaluation documents, plans, source manifests,
  derived views, training runs, checkpoints, and prior review artifacts

## Dependencies

- Frozen `data/downloads/baseline_provisional_split/provisional_split_manifest.csv`
- All rows where `split` is `val_select` or `val_cal`; no `train` rows
- Detector `B-D01` SHA-256
  `646f8bc3fe0a656803d95c294f7852321748cb29d13466a1af8862e2db384a1b`
- Current classifier checkpoint SHA-256
  `c41cfd4a12411883df52bf8643b20a2621b189bbd27c642bae441e92cf06319d`
- Existing detector config and classifier image size; raw uncalibrated probs

## Validation

- Assert exact validation-only count, class/split counts, source existence, and
  zero train parents.
- Run detector, route, classifier, and top-3 for every selected row.
- Report confusion matrix, macro-F1, target-only accuracy, negative rejection,
  per-class, per-split, per-route, detector coverage, and latency.
- Render error/low-margin examples and validate CSV/JSON/image artifacts.
- No recorded-video, temporal, calibration, or robot-motion validation.
- Run `git diff --check` and scoped status review.

## Commit Intent

No commit or push; generated validation evidence remains ignored.

## Validation Result

- Selected exactly 419 parents: 280 `val_select` and 139 `val_cal`; zero
  `train` rows were included.
- Overall raw top-1 accuracy was 398/419 (94.99%), target-only accuracy was
  339/352 (96.31%), provisional `not_target` rejection was 59/67 (88.06%), and
  macro-F1 was 0.9511.
- Split accuracy was 267/280 (95.36%) for `val_select` and 131/139 (94.24%)
  for `val_cal`. These remain diagnostic because `val_select` selected the
  epoch and `val_cal` is reserved if temperature calibration is fitted.
- Detector crop route scored 276/293 (94.20%); centre fallback scored 122/126
  (96.83%). Detector accepted coverage was Ragdoll 89/91, Singapura 42/45,
  Persian 89/101, Sphynx 37/70, Pallas 23/45, and `not_target` 13/67.
- Sequential static chain latency was 51.54 ms mean and 64.21 ms P95 on the
  RTX 4070. This excludes capture, queues, temporal consensus, calibration,
  and robot-domain validation.
- Predictions/errors CSVs, validation error/low-margin sheet, and confusion
  matrix passed count, schema, decode, and visual checks. No source, split,
  threshold, model, checkpoint, robot path, or motion changed.
