# Complete Gate B0 Data Pilots

## Goal

Close the two data-evidence gaps from the Phase 0 Gate B0 audit: produce a
traceable 10-image Oxford-IIIT Pet pilot for each covered target breed and
representative grouped `not_target` pilots with a documented Phase 1 route to
at least 300 negatives. This target does not claim human acceptance, freeze a
training split, train a model, calibrate thresholds, or substitute public
images for the required real robot-camera evidence.

## Dirty-State Note

The worktree already contains the intentional uncommitted plan reorganization,
Baseline hardening, and Phase 0 implementation. All existing dirty paths remain
read-only except the explicitly owned files below. Generated data remains
ignored and must not be staged.

## Owned Files

- `configs/baseline_sources.toml`
- `configs/phase0_pilot_review.toml`
- `src/deskmate_baseline/source_pilot.py`
- `scripts/run_source_pilot.py`
- `scripts/build_pilot_contact_sheets.py`
- `scripts/verify_gate_b0.py`
- targeted tests under `tests/`
- `docs/evaluation/BASELINE_PHASE0_B0_REPORT.md`
- `docs/evaluation/BASELINE_PHASE0_B0_REPORT.json`
- `plan/log.md`
- this target plan
- ignored generated artifacts under `data/downloads/phase0_pilot/**`

## Read-Only Paths

- `References/The requirement/**`
- `docs/plans/**`
- `AGENTS.md`, `README.md`, and prior target plans
- existing source pilots except where the combined generated manifest/report
  must be reproducibly regenerated
- all parent-workspace paths

## Dependencies And Source Contract

- Download the official Oxford-IIIT Pet image archive only from the pinned
  Oxford URL already recorded in `configs/baseline_sources.toml`; compute and
  record its SHA-256 before extraction.
- Extract only the selected Persian, Ragdoll, and Sphynx pilot members into the
  ignored pilot directory. Keep the archive and extracted images out of Git.
- Use Wikimedia Commons API categories for four independently useful
  `not_target` groups: desk scenes, floors, mobile robots, and a non-target cat
  breed. Preserve source page, original URL, author, license, hash, dimensions,
  and source-group metadata for every candidate.
- Every new image remains `quarantine`; only a human team reviewer can mark an
  item accepted. Record visual-risk counts without acceptance authority.
- Selenium remains disabled. Phase 1 bulk acquisition may start only after the
  pilot evidence and human-review process are accepted.

## Work

1. Add safe streaming download, SHA-256, archive-member validation, bounded
   extraction, and Oxford manifest generation.
2. Add multiple named Commons negative groups without changing the canonical
   internal label `not_target`.
3. Regenerate the combined pilot manifest/report and contact sheets.
4. Visually precheck the new pilots for obvious non-image, wrong-category,
   label, and duplicate/session risks; record only non-authoritative triage.
5. Harden the B0 verifier so Oxford requires all three 10-image groups and
   `not_target` requires all four configured groups plus a documented route to
   300 grouped negatives.
6. Re-run the Gate B0 audit. It must remain `NOT_PASSED` until real robot-frame
   evidence and the robot stream contract are supplied.

## Validation

- `python -m compileall -q src tests scripts`
- `python -m pytest -q tests`
- audit the regenerated combined pilot manifest with the real auditor
- parse all changed TOML/JSON using real parsers
- inspect generated contact sheets for each new source/group
- verify archive checksum and that only safe regular image members are selected
- run `python scripts/verify_gate_b0.py`; expect only robot-evidence checks to
  remain open
- confirm `References/The requirement/**` is unchanged
- run `git diff --check` and `git status --short --branch`

## Recorded-Video And Robot Motion

No robot video is available in this target. No physical or autonomous robot
motion is permitted. Public negative images do not satisfy the real-camera B0
check.

## Commit Intent

No branch, commit, push, or PR unless the user requests it. Generated images,
archives, reports under ignored data paths, and private media must not be
committed.

## Validation Results

Implemented and re-audited the bounded data pilots.

- Downloaded the official Oxford-IIIT Pet image archive once into the ignored
  workspace: 791,918,971 bytes, SHA-256
  `67195c5e1c01f1ab5f9b6a5d22b8c27a580d896ece458917e61d459337fa318d`.
- Safely selected and extracted 10 regular JPEG members for each of Persian,
  Ragdoll, and Sphynx; no archive path was trusted for direct extraction.
- Added four 10-image `not_target` groups: desk scenes, floor scenes, mobile
  robots, and a non-target cat breed. The Phase 1 route combines these licensed
  public negatives with grouped real robot-camera background sessions.
- Regenerated a 130-row combined manifest. All rows remain `quarantine`; the
  manifest auditor reported zero errors and zero warnings.
- A Commons floor candidate with a missing canonical license URL was rejected
  before manifest inclusion and replaced by a traceable candidate.
- Generated and visually inspected all 13 contact sheets. The review config
  records usable, label-error, license-missing, and duplicate-risk counts with
  `acceptance_authority=false`.
- Added safe Oxford-member selection coverage; the full suite passes with
  20 tests. Compilation, JSON/TOML parsing, and the manifest audit pass.
- Hardened Gate B0 to require all 13 configured groups, the Oxford archive
  checksum and per-label counts, all four named negative groups, explicit risk
  counts, and the documented route to 300 grouped negatives.

The Gate B0 data checks now pass. The overall gate correctly remains
`NOT_PASSED`; only `real_robot_frame` and `robot_stream_contract` remain open.
No model was trained, Selenium was not used, no robot motion occurred, and no
branch, commit, push, or PR was created.
