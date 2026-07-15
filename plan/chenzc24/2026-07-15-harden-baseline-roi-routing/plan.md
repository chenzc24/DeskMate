# Harden Baseline ROI Routing And Validate The Change

## Goal

Prevent an implausibly small or thin detector proposal from suppressing the
safe centre fallback, remove near-duplicate detector candidates, and compare
the hardened route against the frozen route on the same static diagnostics and
robot-camera stills. Keep breed-classifier/domain errors separate from routing
errors so the experiment cannot claim that routing fixed Singapura or Pallas
recognition.

## Dirty-State Note

Start state from `git status --short --branch`:

```text
## main...origin/main
 M .gitignore
 M plan/log.md
?? docs/evaluation/BASELINE_PROVISIONAL_TRAINING.json
?? docs/evaluation/BASELINE_PROVISIONAL_TRAINING.md
?? docs/evaluation/BASELINE_ROBOT_CAMERA_BATCH2.json
?? docs/evaluation/BASELINE_ROBOT_CAMERA_BATCH2.md
?? docs/evaluation/BASELINE_ROBOT_CAMERA_STILLS.json
?? docs/evaluation/BASELINE_ROBOT_CAMERA_STILLS.md
?? plan/2026-07-15-evaluate-robot-camera-stills/
?? plan/2026-07-15-train-detector-view-classifier/
?? plan/chenzc24/2026-07-15-expand-full-pipeline-sample/
?? plan/chenzc24/2026-07-15-review-detector-boxes/
?? plan/chenzc24/2026-07-15-review-full-pipeline-originals/
```

The existing evaluation documents and plans are concurrent evidence and remain
read-only. `plan/log.md` is append-only for the factual result. The existing
`.gitignore` modification is left untouched. This target owns clean source,
configuration, test, and new evaluation paths, so the overlap is bounded.

## Owner

- Target owner: `chenzc24`

## Owned Files

- `plan/chenzc24/2026-07-15-harden-baseline-roi-routing/plan.md`
- `src/deskmate_baseline/localization.py`
- `configs/baseline_localizer.toml`
- `tests/test_localization.py`
- `scripts/verify_pretrained_cat_localizer.py`
- `scripts/compare_baseline_routing.py`
- `docs/evaluation/BASELINE_ROUTING_ABLATION.json`
- `docs/evaluation/BASELINE_ROUTING_ABLATION.md`
- `data/downloads/baseline_routing_ablation/` (ignored/generated)
- `plan/log.md` (append only)

## Read-Only Files

- `References/The requirement/`
- `docs/plans/BASELINE_PLAN.md`
- `models/yolo26s.pt`
- `runs/baseline_provisional/b-m01-provisional-bd01-oneview-seed-20260715/weights/best.pt`
- `data/downloads/cat_processed/`
- `data/downloads/baseline_detector_box_review/`
- `data/downloads/baseline_full_pipeline_review/`
- `data/downloads/baseline_full_pipeline_expanded/`
- `data/downloads/Camera/`
- all pre-existing dirty and untracked paths listed above

## Shared Dependencies

- Python environment: `.venv`
- GPU: NVIDIA GeForce RTX 4070 Laptop GPU
- `B-D01=models/yolo26s.pt`, frozen COCO cat localizer
- provisional `B-M01` best checkpoint, SHA-256
  `c41cfd4a12411883df52bf8643b20a2621b189bbd27c642bae441e92cf06319d`
- frozen control route: detector confidence 0.25, minimum detector area 0.02,
  15% padding, highest-confidence box, 80% centre fallback

## Expected Work

1. Add deterministic IoU de-duplication for near-identical cat proposals.
2. Add a padded-ROI source-pixel short-side quality gate with an explicit
   fallback reason; preserve same-frame and stability checks. Avoid a normalized
   size gate because the robot evidence contains valid small subjects.
3. Add unit tests for threshold boundaries, false-crop fallback, candidate
   de-duplication, stale input, and unchanged valid-crop behavior.
4. Run a reproducible control-versus-hardened ablation on the same 40 images,
   the expanded 600-image diagnostic, and the final nine robot-camera stills.
5. On robot stills only, classify detector candidates between confidence 0.01
   and 0.25 to test whether a global confidence reduction can recover Pallas.
6. Record routing metrics separately from classifier/domain failures and do
   not tune against or claim release accuracy from these non-held-out samples.

## Validation

- `git diff --check`
- `git status --short --branch`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_localization.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests`
- Run `scripts/compare_baseline_routing.py` with pinned inputs and checkpoints.
- Parse generated JSON/CSV with real parsers and visually inspect the generated
  robot-camera contact sheet.
- Report same-image before/after route, correctness, abstention/conflict, model
  chain mean and P95 latency, and detector missing/accepted/deduplicated counts.
- Recorded-video validation remains pending because only static robot-camera
  JPG/PNG frames are available; no repeated still is counted as an unseen base
  image.

## Robot Motion

No robot connection, motor command, or physical motion is involved.

## Experience Signal (for human review)

The same classifier confidence can be high for a wrong crop or a robot-domain
Pallas image; raw uncalibrated confidence must not be treated as localization
quality or as a release threshold.

## Commit Intent

The user explicitly authorized one direct commit and push to `main`. Stage only
the owned source, configuration, tests, routing ablation evidence, plan, and
append-only log entries listed above; leave concurrent dirty paths untouched.
Generated model outputs remain ignored and no pull request is required.

## Validation Result

- Ten targeted localization tests passed, including IoU de-duplication,
  threshold boundaries, false-crop fallback, stale/mismatched input, and valid
  crop preservation.
- The complete repository suite passed all 87 tests; source/scripts compiled,
  JSON evidence parsed, `git diff --check` passed, and the updated detector
  config completed the five-image offline smoke with five valid proposals.
- The control route reproduced all 640 prior non-robot predictions exactly.
- The hardened route changed only two outcomes: it corrected the 31-pixel false
  Sphynx crop in the biased 40 and admitted the 1.26%-area far Sphynx proposal
  in the robot stills. There were no regressions in the 40, expanded 600, or
  robot nine-still diagnostics.
- Near-duplicate de-duplication affected candidate counts in 12 samples but did
  not change a selected route or prediction.
- Pallas remains 0/2 in the robot-print stills despite 99/100 in the expanded
  in-domain diagnostic. This is left for a separate classifier/domain-data
  target; it cannot honestly be repaired by routing thresholds.
- A robot-only confidence `[0.01, 0.25)` sweep produced four extra proposals
  and zero correct candidate classifications. Both Pallas proposals still
  classified as Persian, so the global confidence threshold remains 0.25.
- The robot comparison sheet was visually inspected. No recorded video or
  robot motion was available.
- `docs/evaluation/BASELINE_LOCALIZER_SMOKE.json` became modified by concurrent
  work at 13:35 after this target's validation smoke had already written to its
  explicitly separate ignored output. It was not edited, staged, or interpreted
  by this target.
