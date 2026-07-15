# Train Detector-View Baseline Classifier

## Goal

Complete one real RTX 4070 training run of `B-M01` on the frozen one-view-per-
parent dataset produced by `B-D01`, then verify the best classifier checkpoint
and record reproducible metrics without promoting the provisional data to
official Gate B1.

## Owned Files And Directories

- `runs/baseline_provisional/b-m01-provisional-bd01-oneview-seed-20260715/`
  (ignored/generated)
- `docs/evaluation/BASELINE_PROVISIONAL_TRAINING.json`
- `docs/evaluation/BASELINE_PROVISIONAL_TRAINING.md`
- `plan/2026-07-15-train-detector-view-classifier/plan.md`
- `plan/log.md` (append only)

## Read-Only Dirty Paths

- frozen detector-derived dataset, view manifest, and handoff archive
- all source acquisition and review material
- existing interrupted original-view run
- official Gate B1 and requirement originals
- robot, Advanced, and presentation paths

## Dependencies

- `B-D01=yolo26s.pt` has already generated the frozen padded crops; it is not
  trained in this target.
- `B-M01=yolo26s-cls.pt` SHA-256 and the derived-view manifest SHA-256 must
  match the committed configuration before execution.
- Training uses the fixed six-label order and 85/10/5 parent split.
- Local NVIDIA RTX 4070, pinned CUDA training environment, and no rented GPU.

## Validation

- Preflight training dry-run and CUDA availability check.
- One real 50-epoch/patience-12 classifier run, allowing configured early stop.
- Parse `results.csv`; record best epoch, train/validation accuracy and loss,
  runtime, configuration, hardware, and checkpoint SHA-256.
- Load `best.pt` and verify the canonical six-class mapping.
- Run targeted/full tests, JSON parsing, `git diff --check`, scoped status, and
  confirm Gate B1 remains fail-closed.

Recorded-video validation is deferred to robot integration because this target
only trains the offline classifier.

## Robot Motion

No robot connection or motion is involved.

## Commit Intent

Do not commit or push training outputs automatically. The user requested the
training run, not another publication step.

## Outcome

- Completed 19 of the configured 50 epochs before patience-12 early stopping;
  wall time was 139.55 seconds on the RTX 4070.
- Epoch 7 `best.pt` reached 95.71% val-select top-1 and 100% top-5; independent
  reload produced 95.81% macro F1 with the canonical six-class mapping.
- The final epoch was worse (92.86% top-1, val loss 0.40026 versus 0.17156 at
  best), confirming that `best.pt`, not `last.pt`, is the correct artifact.
- `best.pt` SHA-256 is
  `c41cfd4a12411883df52bf8643b20a2621b189bbd27c642bae441e92cf06319d`.
- Official Gate B1 remains false; val-cal and all robot-domain sets remain
  unused.
