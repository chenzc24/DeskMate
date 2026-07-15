# Build Provisional Baseline Split

## Goal

Combine the processed human-screened five-breed intake with the original Phase
1 `not_target` candidates and materialize a deterministic 85/10/5 grouped
development split. Defer author/license completion and dHash adjudication as
the user directed, without falsely passing official Gate B1.

## Dirty-State Note

The worktree was clean at target start on `main` at `d5e1d49`. All generated
dataset content remains ignored. This target is disjoint from robot, model,
localizer, presentation, and Advanced work.

## Owner

- Target owner: `Codex`
- Risk decisions: user authorized original `not_target`, deferred author/license
  completion, and no manual dHash adjudication for the first development split

## Owned Files

- `configs/baseline_provisional_dataset.toml`
- `scripts/build_provisional_baseline_split.py`
- `tests/test_provisional_baseline_split.py`
- `docs/evaluation/BASELINE_PROVISIONAL_SPLIT.json`
- `docs/evaluation/BASELINE_PROVISIONAL_SPLIT.md`
- `data/downloads/baseline_provisional_split/` (ignored/generated)
- `plan/2026-07-15-build-provisional-baseline-split/plan.md`
- `plan/log.md` (append only)

## Read-Only Files

- `data/downloads/cat/`
- `data/downloads/cat_processed/`
- `data/downloads/phase1_candidates/`
- existing B1 review decisions and contact sheets
- `References/The requirement/`
- `docs/plans/`
- all model, robot, localizer, and Advanced paths

## Shared Dependencies

- Target candidates come only from `technical_status=candidate` in the
  processed intake manifest.
- Negative candidates come only from existing Phase 1 `not_target` rows with
  `review_status=quarantine`; their pending review is explicitly carried as a
  provisional risk.
- Known same-label source and near-duplicate groups must remain in one split.
- Cross-label dHash-only collisions are ignored as requested; cross-label exact
  hashes remain a hard failure.
- The official training gate and official B1 report remain unchanged and
  fail-closed.

## Expected Work

1. Build a deterministic combined development manifest with source/risk fields.
2. Remove any redundant same-label exact copies and fail on cross-label exact
   content.
3. Allocate connected source/duplicate groups per class into 85% train, 10%
   val-select, and 5% val-cal.
4. Materialize a six-class Ultralytics directory view in ignored storage and
   verify every copy by SHA-256.
5. Record deferred provenance, pending negative review, and incomplete session
   grouping without blocking this provisional data artifact.

## Validation

- Run targeted unit tests and both Python environments' complete suites.
- Run two no-materialization builds and compare manifest/report hashes.
- Verify split ratios, class directories, group non-leakage, source hashes, and
  materialized file counts.
- Parse TOML/CSV/JSON with real parsers.
- Confirm official B1 remains not ready and requirement originals unchanged.
- `git diff --check`
- `git status --short --branch`

Recorded-video validation is not applicable to offline dataset assembly.

## Robot Motion

No robot connection or motion is involved.

## Experience Signal (for human review)

This target is a documented schedule-risk exception: it permits development
training data before full provenance and negative-review completion. It must
not silently become the final release split.

## Commit Intent

No commit or push was requested for this target.

## Validation Results

- The targeted builder suite passed 3 tests; system Python 3.13 and training
  `.venv` Python 3.12 each passed all 74 currently discovered tests.
- The combined split contains 2,787 rows: 2,341 target candidates and 446
  original Phase 1 `not_target` candidates.
- Per-class allocation matches the rounded 85/10/5 targets exactly; 2,787
  materialized copies passed SHA-256 verification.
- Source-group, same-label duplicate-group, and exact-hash cross-split leakage
  counts are all zero.
- Two independent no-materialization builds produced identical manifest and
  report hashes.
- The official B1 auditor still intentionally exits 3; this target did not
  modify or misrepresent the official review gate.
