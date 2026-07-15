# Build Minimal Phase 1 Review Handoff

## Outcome

Create a colleague-facing dataset-review handoff containing only the 2,321
reviewable candidate images, one editable review CSV, and a concise README.
Per the user's correction, store every image directly under its single class
folder (`images/<label>/<image_id>.<ext>`), with no source or batch directories.
Exclude acquisition caches, provenance manifests, contact sheets, benchmarks,
training outputs, smoke videos, and other runtime files.

## Owned Paths

- `scripts/data/build_phase1_review_handoff.py`
- `tests/test_review_handoff.py`
- `data/downloads/phase1_candidates/README.md`
- `data/downloads/phase1_review_handoff_minimal/`
- `data/downloads/phase1_review_handoff_minimal_2026-07-15.zip`
- `plan/2026-07-15-build-minimal-review-handoff/plan.md`
- `plan/log.md`

## Read-Only Existing Paths

- `References/The requirement/`
- `docs/plans/`
- `data/downloads/phase1_candidates/source_manifest.csv`
- `data/downloads/phase1_candidates/review_batches/review_queue.csv`
- all downloaded candidate source directories
- concurrently created robot-JPEG configuration, evidence, documentation, and
  target-plan changes
- all unrelated tracked and ignored files

## Dependencies And Boundaries

- Source candidate images and the current 2,321-row review queue must exist.
- Images are selected only from queue rows; the builder must not infer or alter
  acceptance decisions.
- The generated handoff remains ignored local data and must not enter Git.
- Singapura, Pallas, and Persian still require distinct agreeing second
  reviewers.

## Validation

- Unit-test deterministic layout, copy behavior, README content, and refusal of
  missing/duplicate/unsafe queue rows.
- Assert that the handoff contains exactly six class directories and no nested
  batch/source directories below them.
- Run `python -m pytest -q tests` and compile checks.
- Generate the real handoff, then confirm 2,321 queue rows map one-to-one to
  2,321 images with no missing or extra files.
- Audit the copied review CSV with the existing fail-closed review auditor; the
  expected pre-review result is exit code 3, zero errors, and 2,321 pending.
- Record handoff file count, size, and SHA-256 inventory evidence.
- Recorded-video validation is not applicable to a data-packaging target.
- Run `git diff --check` and scoped Git status review.

## Robot Motion

No robot connection or motion is involved.

## Commit Policy

No commit or push unless the user explicitly requests it. Generated handoff
data remains ignored even if a later source-code commit is requested.

## Validation Results

- Generated 2,321 images totaling 364,150,364 bytes with the expected class
  counts; the image tree contains exactly six class directories and zero
  nested source/batch directories. Contact sheets and unrelated runtime
  artifacts are excluded.
- Queue, inventory, and image counts are all 2,321; there are zero missing,
  extra, or SHA-256-mismatched images.
- The copied queue SHA-256 is
  `b3b2ca5a938830ad1dc5b953c5d0bf5a48533ce8f458bf907bb7013b27a2b36f`.
- The transfer ZIP contains exactly 2,325 files (2,321 images plus README,
  queue, inventory, and summary), is 362,912,283 bytes, and has SHA-256
  `5fa6a44804ed04e93f57d1b5c8342c9edb011bf081e1d400d4a4cc714cdb2af3`.
- The existing review auditor intentionally exits 3 before review, with 2,321
  pending, zero accepted/rejected, zero errors, and
  `ready_to_freeze_split=false`.
- System Python 3.13 and training `.venv` Python 3.12 each pass all 61 tests;
  compile checks pass.
- Requirement originals remain read-only; recorded-video validation and robot
  motion are not applicable.
- Concurrent robot-JPEG target changes appeared during this target and were
  left untouched except for preserving their separate log entry.
