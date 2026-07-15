# Prepare Baseline Phase 1 Candidate Data

## Goal

Acquire and audit the largest reproducible candidate pool available from the
already approved Oxford-IIIT Pet, Wikimedia Commons, and iNaturalist sources,
then produce exact/near-duplicate and per-class gap reports for human review.
This is Phase 1 preparation under the governing rule that later phases may be
prepared without freezing key inputs before Gate B0.

The user has explicitly deferred the real robot-frame and stream-contract
evidence. Those fields remain unknown and Gate B0 remains `NOT_PASSED`; this
target must not rewrite that fact, freeze Gate B1, or claim that public images
replace robot-domain evidence.

## Dirty-State Note

The worktree contains intentional uncommitted plan, Phase 0, source-pilot, and
B0 evidence changes. Existing dirty paths remain read-only except the owned
files below. Generated images, manifests containing local artifact paths, and
archives stay ignored and must not be staged.

## Owned Files

- `configs/baseline_phase1_data.toml`
- `src/deskmate_baseline/source_pilot.py`
- new Phase 1 data acquisition/dedup modules under `src/deskmate_baseline/`
- new Phase 1 scripts under `scripts/`
- targeted tests under `tests/`
- `docs/evaluation/BASELINE_PHASE1_CANDIDATE_REPORT.md`
- `docs/evaluation/BASELINE_PHASE1_CANDIDATE_REPORT.json`
- `plan/log.md`
- this target plan
- ignored generated artifacts under `data/downloads/phase1_candidates/**`

## Read-Only Paths

- `References/The requirement/**`
- `docs/plans/**`
- `AGENTS.md`, `README.md`, and prior target plans
- `configs/baseline_phase0.toml` robot fields and Gate B0 evidence
- all model/training, calibration, robot adapter, and presentation paths
- all parent-workspace paths

## Dependencies And Data Contract

- Reuse the already verified Oxford archive and extract all Persian, Ragdoll,
  and Sphynx members into the ignored Phase 1 candidate area.
- Paginate iNaturalist research-grade Pallas observations while keeping only
  configured photo licenses and one photo per observation.
- Recursively enumerate and batch-query configured Commons categories for all
  target labels and public negative groups, respecting the API/robot policy and
  the existing single-threaded throttle.
- Every candidate remains `quarantine`; automatic quality and duplicate checks
  can reject technical failures but cannot grant human `accepted` status.
- Compute exact SHA-256 and 64-bit perceptual hash. Report exact duplicates,
  near-duplicate clusters, source/session grouping, minimum dimensions, and
  post-filter per-class candidate coverage.
- Keep assignment examples entirely outside the candidate manifest.
- Selenium remains disabled until this post-dedup report measures the remaining
  gap to 400 for each target class.

## Work

1. Add a Phase 1 source/count configuration with bounded request and storage
   limits.
2. Harden Commons continuation/batching and iNaturalist pagination for bounded
   bulk candidate acquisition.
3. Extract all relevant Oxford members and combine all source manifests.
4. Compute deterministic pHash, exact deduplication, near-duplicate clusters,
   and class/source coverage without automatic acceptance.
5. Generate contact-sheet batches and a human-review queue with stable IDs.
6. Produce a machine-readable candidate/gap report that decides Selenium
   go/no-go per class from unique quarantine candidates while clearly
   distinguishing candidate coverage from accepted coverage.
7. Re-run all tests and confirm Gate B0 still fails only the two deferred robot
   evidence checks.

## Validation

- `python -m compileall -q src tests scripts`
- `python -m pytest -q tests`
- parse all TOML/JSON using real parsers
- run the manifest auditor on the Phase 1 candidate manifest
- verify deterministic hashes/clusters on fixtures and repeat generation
- confirm each downloaded file hash/dimensions matches its manifest row
- confirm assignment examples are absent
- generate and inspect representative contact-sheet batches
- run `python scripts/verify_gate_b0.py` and require the same two deferred robot
  failures, with no regression in completed checks
- confirm `References/The requirement/**` is unchanged
- run `git diff --check` and `git status --short --branch`

## Human Review And Gate B1

Human review remains required, especially for Singapura, Pallas, Persian,
other-breed negatives, and near-duplicate/source-session clusters. This target
does not mark rows accepted or freeze the 85/10/5 split. Gate B1 can pass only
after team review and after the deferred Gate B0 evidence is supplied.

## Robot Motion

None. This target performs no camera activation and sends no motor commands.

## Commit Intent

No branch, commit, push, or PR unless requested. Never stage downloaded images,
archives, private media, or ignored generated reports.

## Validation Results

Implemented and validated the Phase 1 candidate-data preparation without
granting human acceptance or freezing Gate B1.

- Added bounded, cacheable acquisition for recursive/batched Commons,
  paginated iNaturalist, official Oxford archive members, and licensed GBIF
  occurrence media. No Selenium path was used.
- Completed one cached full reproducibility rerun from the unified config.
  It combined 2,467 raw source rows into a 2,427-row manifest.
- Technical filtering and deduplication left 2,321 reviewable candidates:
  1,875 target cats plus 446 `not_target` images. All remain `quarantine`.
- Per-label candidate counts are Ragdoll 450, Singapura 250, Persian 447,
  Sphynx 449, Pallas 279, and `not_target` 446.
- Rejected/collapsed evidence includes 39 same-ID aliases, one cross-label ID
  conflict, seven technical failures, two exact duplicate clusters, and 96
  normalized-original-URL duplicate clusters. Eighteen dHash clusters are
  flagged rather than automatically rejected.
- Original-URL deduplication found that 96 of 100 licensed GBIF downloads were
  re-encoded copies of an already-seen source. Only four added unique Pallas
  candidates; downloaded counts were not allowed to inflate coverage.
- The manifest auditor reports zero errors and zero warnings. Assignment
  example images are absent.
- Generated a stable 2,321-row human-review queue and 119 contact sheets with
  zero missing files. Existing decisions survive regeneration; Singapura,
  Pallas, and Persian require distinct agreeing second reviewers.
- The review audit correctly reports 0 accepted, 0 rejected, 2,321 pending,
  zero structural errors, and `ready_to_freeze_split=false`.
- Representative sheets confirmed that same-individual/session sequences are
  under-detected by dHash; human grouping remains mandatory.
- Compilation and the full 31-test suite pass. The B0 verifier remains
  fail-closed only on the two user-deferred checks: `real_robot_frame` and
  `robot_stream_contract`; all other B0 checks pass.

The candidate target total exceeds the 1,200 technical floor but remains 125
below the 2,000 total goal. Balanced 400-per-class coverage is short by 150
Singapura and 121 Pallas images before human rejection. Selenium remains
unauthorized until accepted/post-dedup counts exist. No split, training,
calibration, robot motion, branch, commit, push, or PR was created.
