# Prepare Baseline Phase 2 Training Pipeline

## Outcome

Prepare the deterministic, fail-closed Baseline training pipeline so that an
approved Phase 1 review queue can be frozen and trained immediately, without
pretending that the currently pending candidates have passed Gate B1.

The target may install and verify a project-local Python 3.12 CUDA environment
when that interpreter is already available. It may download and checksum the
official ImageNet-pretrained `yolo26s-cls.pt` asset. It must not start official
training, select a checkpoint, or publish metrics until human review passes.

## Owned Files And Directories

- `configs/baseline_training.toml`
- `models/README.md`
- `models/manifest.yaml`
- `requirements-training.txt`
- `requirements-training.lock.txt`
- new split/training modules under `src/deskmate_baseline/`
- the existing `src/deskmate_baseline/review.py` Gate B1 boundary
- new Phase 2 preparation scripts under `scripts/`
- targeted tests under `tests/`
- `docs/evaluation/BASELINE_PHASE2_READINESS_REPORT.md`
- `docs/evaluation/BASELINE_PHASE2_READINESS_REPORT.json`
- `plan/log.md`
- this target plan
- ignored `.venv/**`, `models/*.pt`, `data/cat_census/**`, and `runs/**`

## Read-Only And Deferred Paths

- `References/The requirement/**`
- `docs/plans/**`
- Phase 0/1 target plans and reports
- `data/downloads/phase1_candidates/source_manifest.csv`
- human decisions in
  `data/downloads/phase1_candidates/review_batches/review_queue.csv`
- robot frame, stream-contract, calibration, and final-test evidence
- all parent-workspace paths

## Dependencies And Contracts

- Python 3.13 is not used for the CUDA training environment because the
  official Windows PyTorch support range is currently Python 3.9--3.12.
- Prefer an existing Python 3.12 interpreter and create `.venv`; do not alter
  the system interpreter or install a global training stack.
- Use official CUDA-enabled PyTorch wheels and the official Ultralytics
  `yolo26s-cls.pt` classification model. Pin installed versions and record the
  weight source URL, SHA-256, license, input, output, and priority.
- Canonical directory/class order remains
  `ragdoll / singapura / persian / sphynx / pallas / not_target`.
- Freeze exactly 85% train, 10% `val_select`, and 5% `val_cal`, deterministically
  with seed `20260714`, while keeping duplicate and source/session groups in a
  single split.
- Split creation must fail unless every selected row has valid human review,
  configured second-review classes have distinct agreeing reviewers, accepted
  class floors pass, referenced files exist, and duplicate clusters cannot
  cross splits.
- Generated dataset views and run artifacts remain ignored. The tracked split
  recipe/report contains portable relative identifiers and checksums, never
  private absolute paths.
- The first official training run remains blocked until Gate B1 passes. A
  deterministic synthetic fixture or framework smoke test is allowed but may
  not be reported as model performance.

## Work

1. Implement and test the review-to-split merge and a deterministic grouped
   85/10/5 allocator with fail-closed Gate B1 validation.
2. Implement an idempotent dataset-view materializer and integrity audit.
3. Add a pinned training config and a command/config generator for one
   `yolo26s-cls` seed, with no subprocess execution by default.
4. If Python 3.12 is locally available, create `.venv`, install the pinned CUDA
   stack, verify CUDA visibility, download the official base weight, and record
   its checksum and environment versions.
5. Produce a readiness report that separates implemented capabilities from
   unresolved human-review and robot evidence.

## Validation

- `python -m compileall -q src tests scripts`
- `python -m pytest -q tests`
- parse TOML, YAML, and JSON with real parsers
- exercise missing/pending/disagreeing/duplicate-review cases
- exercise grouped deterministic splitting, ratio bounds, repeat generation,
  missing files, class-order mismatch, and cross-split leakage detection
- verify the training command/config in dry-run mode
- if `.venv` exists, verify installed versions and `torch.cuda.is_available()`
- if the base weight exists, verify its SHA-256 and one classification inference
  without treating ImageNet output as Cat Census evidence
- confirm Gate B0 still fails only the two user-deferred robot checks
- confirm Gate B1 and official training still fail closed on pending reviews
- confirm `References/The requirement/**` is unchanged
- run `git diff --check` and `git status --short --branch`

## Robot Motion

None. No camera activation, robot connection, or motor command is permitted.

## Commit Intent

No branch, commit, push, or PR unless the user explicitly requests it. Do not
stage `.venv`, weights, datasets, private media, or run artifacts.

## Validation Results

Completed the non-blocked Phase 2 preparation without accepting candidates or
starting official training.

- Added a fail-closed review-to-split merge and deterministic grouped 85/10/5
  allocator. Source/session IDs, duplicate clusters, and exact hashes are kept
  together; cross-label linked groups are rejected.
- Added an idempotent hard-link/copy dataset materializer with per-file SHA-256
  verification, canonical indexed class directories, and rejection of
  untracked extra files.
- Added a pinned dry-run training plan. `--execute` additionally requires a
  machine-readable ready Gate B1 report, materialized train/val directories,
  and the verified base weight.
- The real 2,321-row review queue is correctly rejected with exit code 3: zero
  accepted, zero rejected, and 2,321 pending. No split manifest was written.
- Created `.venv` from the installed Python 3.12.10 interpreter. PyTorch
  2.11.0+cu128, Torchvision 0.26.0+cu128, Ultralytics 8.4.95, and all transitive
  packages match the tracked lock.
- PyTorch sees the NVIDIA GeForce RTX 4070 Laptop GPU and executed a CUDA tensor
  using the CUDA 12.8 runtime.
- Downloaded the official 13,622,082-byte `yolo26s-cls.pt` base asset. Its
  SHA-256 is
  `816790029d5df3fef358f03c8144b96339d8824ee25577aeda8be0963e5c5f09`.
- A GPU smoke inference on an assignment example returned `Results.probs` and
  no boxes. The example remains outside training data and the ImageNet result
  is explicitly not treated as Baseline performance evidence.
- Both the default and pinned environments pass all 38 tests. TOML, YAML, and
  JSON parsing, seven report checksums, parent-directory launches, and the
  reproducible bootstrap check pass.

Gate B0 remains deferred only on `real_robot_frame` and
`robot_stream_contract`. Gate B1 remains not passed on human review. No
Selenium, official training, calibration, robot connection, motion, branch,
commit, push, or PR was performed.
