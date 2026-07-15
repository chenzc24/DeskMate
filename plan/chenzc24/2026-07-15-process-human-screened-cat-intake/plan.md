# Process Human-Screened Cat Intake

## Goal

Turn `data/downloads/cat` into a deterministic, auditable five-target-class
intake without modifying the human-screened originals. Produce canonical label
mapping, decode/dimension/hash evidence, exact-duplicate exclusion, perceptual
duplicate grouping, and a clean candidate view for later provenance completion
and grouped split freezing.

## Dirty-State Note

The worktree already contains active robot-default, review-handoff, pretrained
localizer, and detector-derived-view work. This target owns none of those
paths. It uses new, disjoint processing files and treats every pre-existing
dirty path as read-only except for an append-only maintenance-log entry.

Notable existing read-only dirty paths include:

```text
README.md
configs/baseline_phase0.toml
docs/plans/BASELINE_PLAN.md
models/README.md
models/manifest.yaml
plan/2026-07-15-activate-robot-jpeg-defaults/
plan/2026-07-15-build-minimal-review-handoff/
plan/2026-07-15-add-pretrained-cat-localizer/
plan/2026-07-15-smoke-pretrained-cat-localizer/
plan/2026-07-15-add-detector-derived-classifier-views/
scripts/data/build_phase1_review_handoff.py
scripts/evaluation/verify_pretrained_cat_localizer.py
src/deskmate_baseline/localization.py
tests/test_localization.py
tests/test_review_handoff.py
```

## Owner

- Target owner: `chenzc24`
- Execution agent: `Codex`
- Label acceptance authority: the human reviewers who supplied the intake
- Provenance/license completion owner: unassigned

## Owned Files

- `configs/baseline_human_screened_intake.toml`
- `scripts/data/process_human_screened_cat_intake.py`
- `tests/test_human_screened_cat_intake.py`
- `docs/evaluation/BASELINE_HUMAN_SCREENED_INTAKE.json`
- `docs/evaluation/BASELINE_HUMAN_SCREENED_INTAKE.md`
- `data/downloads/cat_processed/` (ignored/generated)
- `plan/chenzc24/2026-07-15-process-human-screened-cat-intake/plan.md`
- `plan/log.md` (append only)

## Read-Only Files

- `data/downloads/cat/` human-screened originals
- `data/downloads/phase1_candidates/` and its active review queue
- `data/cat_census/`
- `References/The requirement/`
- `docs/plans/`
- all model weights, training runs, robot artifacts, and pre-existing dirty
  files not explicitly owned above

## Shared Dependencies

- Canonical target order: `ragdoll / singapura / persian / sphynx / pallas`.
- Existing technical floor: minimum width and height 160 pixels; images remain
  resized to 224 only inside the future model pipeline.
- Perceptual dHash distance 4 is a grouping/review signal, not automatic proof
  that two images are duplicates.
- Human screening establishes a label decision but does not reconstruct source
  URL, author, license, or capture-session provenance lost during merging.

## Expected Work

1. Add an explicit folder-to-canonical-label configuration.
2. Build a deterministic scanner that verifies image decoding, records hashes
   and dimensions, rejects below-floor files, excludes redundant exact copies,
   and groups near duplicates without deleting originals.
3. Materialize a canonical clean candidate view using copies or hard links in
   an ignored output directory.
4. Emit machine-readable inventory/audit artifacts and a tracked aggregate
   evaluation summary without exposing personal paths.
5. Stop before split freeze or training if provenance, `not_target`, or
   duplicate/session review remains incomplete.

## Validation

- Run targeted unit tests for the new processor.
- Run both available Python environments' complete test suites.
- Run the processor twice into separate ignored outputs and compare manifest
  and audit content hashes for determinism.
- Verify all raw image hashes are unchanged before and after processing.
- Parse TOML, CSV, and JSON artifacts using real parsers.
- Confirm canonical counts and no cross-label exact duplicates.
- Confirm requirement originals remain unchanged.
- `git diff --check`
- `git status --short --branch`

Recorded-video validation is not applicable to offline still-image intake.

## Robot Motion

No robot connection or motion is involved.

## Experience Signal (for human review)

Sequential renaming and teammate merging removed provenance and likely
source-session boundaries for most images. Treating every file as independent
would permit leakage across validation; provenance/session reconstruction or a
conservative grouping decision is required before Gate B1 split freeze.

## Commit Intent

No commit or push was requested for this intake-processing target. Generated
images, manifests, duplicate-review rows, and verification outputs remain
ignored.

## Validation Results

- The targeted intake suite passed 4 tests; system Python 3.13 and the training
  `.venv` Python 3.12 each passed all 71 currently discovered tests.
- All 2,427 source images decoded. Technical filtering retained 2,341 clean
  target candidates, rejected 79 below-floor images and 7 redundant exact
  copies, and found no cross-label exact duplicates.
- Two independent no-materialization runs produced identical manifest,
  duplicate-review, and audit SHA-256 values. The source snapshot remained
  `ffc42a8e11af1f569fb2360dbfa7ca163036e33ba7dcdb2ec524f8533543e59b`.
- The ignored materialized view contains 2,341 candidate copies with zero
  integrity errors. Gate B1 remains closed on missing `not_target` data,
  incomplete provenance/session groups, and unresolved near-duplicate review.
- TOML/JSON parsing, compile checks, and `git diff --check` passed. No robot
  connection or motion occurred.
