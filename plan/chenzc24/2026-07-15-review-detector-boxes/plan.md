# Review Detector Boxes On Original Data

## Outcome

Create human-readable contact sheets from a deterministic, stratified subset of
the original five-breed images, using the frozen `B-D01` detector to draw its
actual cat boxes, confidence values, and hit/miss/multi-box status.

## Owned Paths

- `plan/chenzc24/2026-07-15-review-detector-boxes/plan.md`
- `data/downloads/baseline_detector_box_review/` (ignored/generated)
- `plan/log.md` (append-only after validation, without rewriting concurrent work)

## Existing Dirty Paths Left Read-Only

- `.gitignore`
- `docs/evaluation/BASELINE_PROVISIONAL_TRAINING.*`
- `docs/evaluation/BASELINE_ROBOT_CAMERA_BATCH2.*`
- `docs/evaluation/BASELINE_ROBOT_CAMERA_STILLS.*`
- `plan/2026-07-15-evaluate-robot-camera-stills/`
- `plan/2026-07-15-train-detector-view-classifier/`
- all training runs, checkpoints, data manifests, and source images

## Dependencies

- Original target source: `data/downloads/cat_processed/clean_candidates/`
- Detector: `B-D01=models/yolo26s.pt`
- Expected detector SHA-256:
  `646f8bc3fe0a656803d95c294f7852321748cb29d13466a1af8862e2db384a1b`
- Ultralytics 8.4.95, COCO native `cat` class ID 15
- Local RTX 4070 when available; do not interrupt concurrent classifier training

## Method And Validation

- Select original images deterministically and stratify across all five breeds.
- Include ordinary random samples plus difficult Sphynx/Pallas and multi-box
  examples so the review is not success-only.
- Run fresh detector inference and draw every retained cat box at the frozen
  confidence threshold; explicitly label misses.
- Verify every displayed source path is under the immutable original source,
  record detector/config identity in the output summary, and visually inspect
  the rendered sheets.
- Run `git diff --check` and scoped `git status --short --branch`.
- Recorded-video validation is not applicable to this original-image review;
  real robot-video admission remains a separate gate.

## Robot Motion

No robot connection or motion.

## Commit Intent

No commit or push. Contact sheets are generated review artifacts and remain
ignored; existing concurrent dirty work stays untouched.

## Validation Result

- Fresh RTX 4070 inference completed on 40 immutable original target images:
  15 ordinary prior hits, 12 deliberately difficult Sphynx/Pallas cases, and
  13 prior multi-box cases.
- With frozen `conf=0.25`, `imgsz=640`, cat ID 15, and `max_det=5`, the biased
  review sample produced 20 single hits, 9 multi-box results, and 11 misses.
  These counts describe the review selection and are not a population metric.
- Three contact sheets, a per-image detection CSV, and a machine-readable report
  were produced under `data/downloads/baseline_detector_box_review/`.
- Visual inspection confirmed the boxes are legible and exposed expected
  Sphynx/Pallas misses plus multi-cat/nested-cat multi-box behavior.
- No source, split, derived training view, checkpoint, or concurrent dirty path
  was modified; no robot or recorded-video claim was made.
