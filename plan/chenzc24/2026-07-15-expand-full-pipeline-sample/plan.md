# Expand Full-Pipeline Static Sample

## Outcome

Expand the detector-to-classifier diagnostic from 40 target originals to a
deterministic, balanced 600-image sample: 100 images for each of the five target
breeds plus 100 provisional `not_target` images. Run the unchanged active
static chain and expose class, route, detector, confidence, margin, latency, and
failure patterns.

## Owned Paths

- `plan/chenzc24/2026-07-15-expand-full-pipeline-sample/plan.md`
- `data/downloads/baseline_full_pipeline_expanded/` (ignored/generated)
- `plan/log.md` (append only)

## Existing Dirty Paths Left Read-Only

- `.gitignore`
- all provisional-training and robot-camera evaluation documents/plans
- both preceding user-scoped detector/full-pipeline review targets and artifacts
- all source images, manifests, derived datasets, training runs, and checkpoints

## Dependencies And Sampling

- Source authority: original rows in the frozen detector `view_manifest.csv`
- Target sources: `data/downloads/cat_processed/`
- Negative sources: `data/downloads/phase1_candidates/`
- Fixed seed `20260715`; exclude the preceding 40 target parent IDs
- Per class: 85 train, 10 val-select, and 5 val-cal parents, sampled without replacement
- Detector and classifier hashes/configuration remain exactly those recorded in
  the preceding full-pipeline review target
- `not_target` is provisional and its human review/provenance gate remains open

## Validation

- Assert 600 unique parents, exactly 100 per class and 85/10/5 per-class split.
- Verify source files and both model hashes before inference.
- Run the unchanged sequential static chain and record every raw/accepted box,
  route, ROI, top-3, confidence, margin, correctness, and wall time.
- Report six-class confusion matrix, macro F1, target-only accuracy, negative
  rejection, per-class metrics, route metrics, detector coverage, and latency.
- Render balanced random, failure, low-margin, and fallback contact sheets with
  the actual classifier input inset; visually inspect generated sheets.
- Parse CSV/JSON and validate counts; run `git diff --check` and scoped status.
- Results are diagnostic because train/val-select images and provisional
  negatives are included. Recorded-video, temporal consensus, and robot-final
  validation remain out of scope.

## Robot Motion

No robot connection or motion.

## Commit Intent

No commit or push. Generated evaluation artifacts remain ignored and concurrent
dirty work stays untouched.

## Validation Result

- Frozen sampling produced exactly 600 unique parents, 100 per class and exactly
  85 train / 10 val-select / 5 val-cal per class, excluding the preceding 40.
- The unchanged chain produced 588/600 correct: six-class accuracy 98.0%,
  target-only accuracy 98.4%, provisional negative rejection 96.0%, and macro
  F1 0.9800. These are mixed-split diagnostic figures, not release metrics.
- Detector-crop routes were 401/409 correct; centre fallbacks were 187/191.
  Accepted detector coverage was 100% Ragdoll, 97% Singapura, 87% Persian, 54%
  Sphynx, 51% Pallas, and 20% provisional negatives.
- Twelve errors comprised four Singapura, one Persian, two Sphynx, one Pallas,
  and four provisional negatives; eight used detector crops and four fallbacks.
- Sequential warmed static inference measured 49.32 ms mean and 55.62 ms P95
  detector-plus-classifier wall time on the RTX 4070. This excludes capture,
  quality gates, queues, UI, and temporal consensus.
- Predictions/errors CSVs, report JSON, confusion matrix, and four review sheets
  passed count/schema/decode checks and visual inspection.
- No source, split, threshold, model, checkpoint, robot protocol, concurrent
  dirty path, or motion was changed.
