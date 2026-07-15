# Review Full Detector-To-Classifier Pipeline On Original Data

## Outcome

Run the current `B-D01 -> padded detector crop or centre fallback -> B-M01`
chain on exactly the same 40 immutable original images used in the detector-box
review, then render contact sheets showing route, boxes, classifier top-1/top-3,
confidence, and correctness against the source breed label.

## Owned Paths

- `plan/chenzc24/2026-07-15-review-full-pipeline-originals/plan.md`
- `data/downloads/baseline_full_pipeline_review/` (ignored/generated)
- `plan/log.md` (append only)

## Existing Dirty Paths Left Read-Only

- `.gitignore`
- all existing provisional-training and robot-camera evaluation documents/plans
- `plan/chenzc24/2026-07-15-review-detector-boxes/`
- detector review images, CSV, JSON, source images, derived dataset, training
  runs, and checkpoints

## Dependencies And Frozen Configuration

- Input order: the 40 rows in
  `data/downloads/baseline_detector_box_review/detections.csv`
- Detector `B-D01=models/yolo26s.pt`, SHA-256
  `646f8bc3fe0a656803d95c294f7852321748cb29d13466a1af8862e2db384a1b`
- Detector config: cat ID 15, `conf=0.25`, `imgsz=640`, minimum accepted box
  area ratio 0.02, maximum 5 candidates
- Routing: highest-confidence accepted box, 15% padding; otherwise centred 80%
  fallback
- Classifier checkpoint:
  `runs/baseline_provisional/b-m01-provisional-bd01-oneview-seed-20260715/weights/best.pt`
  with expected SHA-256
  `c41cfd4a12411883df52bf8643b20a2621b189bbd27c642bae441e92cf06319d`
- Raw uncalibrated classifier probabilities are review evidence only; no
  temporal consensus or release threshold is claimed.

## Validation

- Assert exact parent ID, source path, label, and order match the preceding
  detector review.
- Check both model hashes and the canonical six-output classifier mapping.
- Record per-image detector candidates, route, crop coordinates, top-3,
  prediction, confidence, correctness, and model-chain latency.
- Report accuracy by route and class only as a deliberately biased diagnostic,
  not held-out or release accuracy.
- Visually inspect every contact sheet; parse CSV/JSON; run `git diff --check`
  and scoped status review.
- Recorded-video and temporal validation remain out of scope; these are static
  original images.

## Robot Motion

No robot connection or motion.

## Commit Intent

No commit or push. Generated full-pipeline review artifacts remain ignored and
all concurrent work stays untouched.

## Validation Result

- Both model hashes and the canonical six-output mapping passed; all 40 parent
  IDs, source paths, labels, and ordering exactly matched the detector-only
  review.
- The deliberately biased static sample produced 37/40 correct top-1 outputs:
  detector crops 29/32 and centre fallbacks 8/8. These are diagnostic counts,
  not held-out or release accuracy.
- Errors were `target-sphynx-000158` (a false detector crop routed to
  `not_target`) and multi-box `target-singapura-000071`/`000083` (routed to
  `persian`/`not_target`).
- Three full-pipeline contact sheets, per-image predictions CSV, and JSON report
  were generated and visually inspected. Every tile shows the actual classifier
  input inset and raw uncalibrated top-3.
- Sequential single-image diagnostic wall time measured 84.74 ms mean and
  192.54 ms P95 for detector plus classifier. This is not a real-time benchmark
  because capture, quality gates, queues, temporal consensus, and warmed replay
  timing were not exercised.
- No threshold, source, dataset, model, checkpoint, concurrent dirty path, robot
  protocol, or motion was changed.
