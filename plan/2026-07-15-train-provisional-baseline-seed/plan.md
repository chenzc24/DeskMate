# Train Provisional Baseline Seed

## Goal

Train one development-only B-M01 seed on the provisional six-class split using
the local RTX 4070, then record reproducible checkpoint and validation evidence
without claiming official Gate B1 or final evaluation readiness.

## Dirty-State Note

The worktree contains the immediately preceding provisional split target. This
training target depends on those new files but owns no split-generation logic.
All unrelated paths remain read-only.

## Owner

- Target owner: `Codex`
- Development-risk authorization: user deferred author/license and dHash
  adjudication and authorized autonomous continuation

## Owned Files

- `configs/baseline_training_provisional.toml`
- `scripts/training/train_provisional_baseline.py`
- `tests/test_provisional_training.py`
- `docs/evaluation/BASELINE_PROVISIONAL_TRAINING.json`
- `docs/evaluation/BASELINE_PROVISIONAL_TRAINING.md`
- `runs/baseline_provisional/` (ignored/generated)
- `plan/2026-07-15-train-provisional-baseline-seed/plan.md`
- `plan/log.md` (append only)

## Read-Only Files

- provisional split config, builder, manifest, report, and materialized dataset
- official `configs/baseline_training.toml` and official Gate B1 artifacts
- source/review manifests and all raw data
- base model weight `models/yolo26s-cls.pt`
- robot, localizer, Advanced, requirement, and high-level plan paths

## Shared Dependencies

- Training may start only when the provisional report says
  `provisional_training_data_ready=true`, `official_gate_b1_ready=false`, and
  its manifest checksum matches the materialized manifest.
- Output is namespaced `B-M01-PROVISIONAL` under `runs/baseline_provisional`.
- The official training entry point remains fail-closed and unchanged.
- `val` selects the epoch; `val_cal` remains outside Ultralytics training and is
  reserved for later calibration/evaluation.

## Expected Work

1. Add a pinned provisional training config derived from the Baseline recipe.
2. Add a guard that validates the provisional report, dataset layout, base
   weight, and manifest checksum before execution.
3. Smoke the training command, then execute one 50-epoch/patience-12 seed on
   the RTX 4070.
4. Record best/last checkpoint checksums, best epoch metrics, curves, runtime,
   and hardware from generated evidence.
5. Stop before calibration, threshold freeze, robot-final evaluation, or
   release promotion.

## Validation

- Targeted tests plus both Python environments' complete suites.
- Dry-run plan validation and one real CUDA training run.
- Parse Ultralytics `results.csv` and verify best/last checkpoints load with the
  canonical six-class mapping.
- Evaluate only on the provisional val-select directory in this target.
- Confirm official B1 remains fail-closed and requirement originals unchanged.
- `git diff --check`
- `git status --short --branch`

Recorded-video validation is deferred to the later robot-calibration target.

## Robot Motion

No robot connection or motion is involved.

## Experience Signal (for human review)

Provisional model metrics can guide engineering but must not be copied into the
final report after the official data/review contract changes; the final release
requires retraining on the frozen official split.

## Commit Intent

No commit or push was requested for this target.

## Outcome

Superseded before completion. The original-view run was stopped after one full
epoch and part of epoch two when the user clarified that classifier training
must use frozen `B-D01`-derived views. Its ignored checkpoints and metrics are
not release evidence and are explicitly excluded from the parallel-training
handoff. Training now starts from the detector-view target documented in
`plan/2026-07-15-freeze-detector-view-training-handoff/plan.md`.
