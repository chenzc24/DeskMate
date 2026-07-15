# Harden Singapura And Pallas Classification

## Goal

Train and compare development-only `B-M01` candidates that reduce Singapura
and Pallas confusion while preserving the other four internal outputs. Address
class-count/view imbalance and the robot printed-page domain with deterministic
train-only materialization; do not change the validated detector routing or use
the nine robot diagnostic stills as training data.

## Dirty-State Note

Start state from `git status --short --branch`:

```text
## main...origin/main
 M .gitignore
 M docs/evaluation/BASELINE_LOCALIZER_SMOKE.json
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
?? plan/chenzc24/2026-07-15-validation-only-full-pipeline/
```

These paths are concurrent evidence or generated-artifact policy and remain
read-only. The new target uses new code/config/evidence paths and appends only
to `plan/log.md`; it does not overlap the existing modified smoke report.

## Owner

- Target owner: `chenzc24`

## Owned Files

- `plan/chenzc24/2026-07-15-harden-singapura-pallas-classifier/plan.md`
- `configs/baseline_classifier_hardening.toml`
- `configs/baseline_classifier_soups.toml`
- `configs/baseline_inference_hardened_candidate.toml`
- `models/manifest.yaml`
- `src/deskmate_baseline/classifier_hardening.py`
- `scripts/data/build_classifier_hardening_dataset.py`
- `scripts/training/train_classifier_hardening.py`
- `scripts/evaluation/evaluate_classifier_candidates.py`
- `scripts/training/build_classifier_weight_soups.py`
- `tests/test_classifier_hardening.py`
- `docs/evaluation/BASELINE_CLASSIFIER_HARDENING.json`
- `docs/evaluation/BASELINE_CLASSIFIER_HARDENING.md`
- `data/downloads/baseline_classifier_hardening/` (ignored/generated)
- `data/downloads/baseline_classifier_hardening_determinism_b/` (ignored/generated)
- `runs/baseline_classifier_hardening/` (ignored/generated)
- `plan/log.md` (append only)

## Read-Only Files

- `References/The requirement/`
- `docs/plans/BASELINE_PLAN.md`
- `data/downloads/baseline_detector_views/`
- `data/downloads/cat_processed/`
- `data/downloads/phase1_candidates/`
- `data/downloads/baseline_full_pipeline_validation_only/`
- `data/downloads/baseline_routing_ablation/`
- `data/downloads/Camera/`
- `models/yolo26s-cls.pt`
- `runs/baseline_provisional/b-m01-provisional-bd01-oneview-seed-20260715/weights/best.pt`
- all pre-existing dirty and untracked paths listed above

## Shared Dependencies

- Python environment `.venv`, OpenCV, Ultralytics 8.4.95, Torch 2.11.0+cu128
- NVIDIA GeForce RTX 4070 Laptop GPU
- frozen parent split and detector-derived `view_manifest.csv`
- canonical six-output order:
  `ragdoll/singapura/persian/sphynx/pallas/not_target`
- current checkpoint SHA-256
  `c41cfd4a12411883df52bf8643b20a2621b189bbd27c642bae441e92cf06319d`
- nine robot stills are evaluation-only diagnostics with visible printed labels;
  none may enter train, val-select, or val-cal materialization

## Expected Work

1. Quantify train-only parent counts, selected-view ratios, and existing
   Singapura/Pallas errors on val-select, val-cal, and robot diagnostics.
2. Materialize deterministic candidates without split leakage:
   a class-balanced one-view control and a balanced multi-view/printed-page
   domain-randomized variant using train parents only.
3. Train candidates from the same pinned ImageNet checkpoint and seed with the
   same 224px classifier task; never initialize from robot-evaluated `best.pt`.
4. Evaluate current and candidate checkpoints on the identical frozen
   val-select/val-cal parents through the hardened detector route, then on the
   unchanged nine robot stills. Report per-class recall/confusion, macro F1,
   Pallas/Singapura results, other-class regressions, and latency.
5. Because the Baseline contract permits only one active classifier, test a
   bounded set of single-checkpoint weight soups when candidates are
   complementary; keep any multi-model decision rule as a diagnostic ceiling,
   never as the release runtime.
6. Recommend replacement only if a candidate improves the target failure cases
   without material overall or per-class regression. Otherwise keep the current
   checkpoint and expose the remaining robot-domain data requirement.

## Validation

- `git diff --check`
- `git status --short --branch`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_classifier_hardening.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests`
- deterministic double-build manifest/hash comparison
- assert parent/session groups never cross splits and generated print views use
  train parents only
- parse TOML/JSON/CSV with real parsers and verify model SHA-256/class mapping
- compare all checkpoints on exactly the same validation and robot inputs
- visually inspect a stratified sheet of generated printed-page views and every
  changed robot prediction
- recorded-video temporal validation remains pending because only static robot
  frames are available

## Robot Motion

No robot connection, command, or physical motion.

## Experience Signal (for human review)

The robot Pallas sample is only two base images. Improving both is useful
diagnostic evidence but cannot establish release generalization; a separate
session-grouped robot-domain final set remains mandatory.

## Commit Intent

No commit or push. Train/evaluate first and present the replacement decision to
the user; checkpoints and generated datasets remain ignored.

## Validation Result

- Built both variants twice with identical manifest SHA-256
  `1dd6e54b36fa93299639c8b2316fb8841ff61516ef7dbe920658deac6ca3b2ba`;
  each has 573 train views per class, and zero robot stills entered training.
- Visually reviewed generated printed-page examples: the synthetic training
  image contains no breed-name text; review-sheet captions are outside the
  actual classifier inputs.
- Trained balanced one-view for 35 epochs (best epoch 25, 428.091 s, SHA-256
  `836f508e390907baa76c0af29c0f0a8fd87feb1b6ea44f3f0ceb8954f233882d`)
  and balanced-print for 20 epochs (best epoch 10, 228.3596 s, SHA-256
  `b2abc617772ff97f5e63cb69d0616f031dd9a1af80c6dac6095405a093b6f858`).
- The selected single-model 50/50 weight soup rebuilt deterministically, kept
  the canonical class mapping, and has SHA-256
  `0d598ec33773e82b147380c9fa866c71482fe42800dae1086fb63b90935b3296`.
- On the identical hardened ROI route, current to candidate changed validation
  correct from 399/419 to 403/419 and macro F1 from 0.9534 to 0.9656. Pallas
  changed 44/45 to 45/45 and robot Pallas 0/2 to 2/2; Singapura changed 43/45
  to 42/45 and remained 1/1 on its single robot still.
- Robot total changed 7/9 to 8/9, with one new Persian-to-`not_target`
  regression. Candidate latency stayed effectively unchanged (11.54 ms mean,
  20.29 ms P95 versus 11.64/20.97 ms current).
- `python -m pytest -q tests` passed 88 tests; compile, TOML/YAML/JSON parsing,
  checkpoint hash/mapping checks, visual robot review, `git diff --check`, and
  scoped status review passed during the target.
- The candidate remains development-only because the nine robot stills were
  used during design and contain only one Singapura and two Pallas base images.
  Concurrent balanced-300, other-negative, camera, source, and parent-worktree
  paths remained read-only.
