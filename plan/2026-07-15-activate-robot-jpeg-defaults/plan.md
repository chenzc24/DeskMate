# Activate Robot JPEG Defaults

## Goal

Restart the Baseline robot-integration target with a provisional requested
camera profile of 480 x 480 JPEG quality 85 at 8 FPS, while keeping unknown
transport and real-camera evidence fail-closed and recording that Gate B1 human
image review is now in progress.

## Dirty-State Note

Start state from `git status --short --branch`:

```text
## main...origin/main
?? plan/2026-07-15-build-minimal-review-handoff/
?? scripts/data/build_phase1_review_handoff.py
?? tests/test_review_handoff.py
```

These untracked paths belong to the active human-review handoff work. They are
unrelated to this target, remain read-only, and will not be staged or validated
as this target's output.

## Owner

- Target owner: `Codex`, with camera delivery details supplied by Robotics

## Owned Files

- `configs/baseline_phase0.toml`
- `README.md`
- `docs/evaluation/BASELINE_PHASE0_MANUAL_ACTIONS.md`
- `docs/evaluation/BASELINE_PHASE0_B0_REPORT.md`
- `docs/evaluation/BASELINE_PHASE0_B0_REPORT.json`
- `docs/evaluation/BASELINE_VIDEO_SOURCE_READINESS.md`
- `docs/evaluation/BASELINE_VIDEO_SOURCE_READINESS.json`
- `plan/2026-07-15-activate-robot-jpeg-defaults/plan.md`
- `plan/log.md`

## Read-Only Files

- `References/The requirement/`
- `docs/plans/`
- `configs/baseline_phase1_data.toml`
- all source, scripts, and tests
- `plan/2026-07-15-build-minimal-review-handoff/`
- `scripts/data/build_phase1_review_handoff.py`
- `tests/test_review_handoff.py`
- the ignored B1 queue, contact sheets, datasets, weights, and media

## Shared Dependencies

- Current inference input remains 224 x 224 with centre ROI scales 1.0, 0.8,
  and 0.6.
- JPEG is an image encoding, not a delivery protocol; protocol and endpoint
  remain unknown until Robotics supplies them.
- B1 acceptance remains governed by decisions written into the ignored review
  queue, not by a documentation status label.

## Expected Work

1. Record the provisional requested robot-camera profile and freshness policy.
2. Expose which camera fields are configured versus still unverified.
3. Mark B1 human review as in progress without claiming accepted images.
4. Refresh the fail-closed B0 audit and consistency documentation.

## Validation

- Parse changed TOML and JSON using real parsers.
- Run both available Python environments' complete test suites.
- Run the B0 verifier and confirm only real frame and stream delivery remain
  failed.
- Run the B1 review auditor and record its actual current counts.
- Confirm requirement originals remain unchanged.
- `git diff --check`
- `git status --short --branch`

Recorded-video validation is not applicable: no real robot JPG has yet been
provided, and fixture replay is not robot evidence.

## Robot Motion

No robot motion is involved. The DL process remains unable to issue motor
commands.

## Experience Signal (for human review)

The temporal voter must not count repeated downloads of one cached JPG as
distinct frames. The transport integration needs a source frame ID/timestamp or
an explicit duplicate-frame guard before live confirmation.

## Commit Intent

No commit or push was requested for this target.

## Validation Results

- System Python 3.13 and training `.venv` Python 3.12 each passed all 61
  currently discovered tests, including the read-only untracked review-handoff
  test present at validation time.
- The B0 verifier intentionally exited 3 with exactly `real_robot_frame` and
  `robot_stream_contract` failed; its evidence contains the requested profile
  and retains unknown protocol/endpoint values.
- The B1 auditor intentionally exited 3 with 2,321 pending, zero accepted, zero
  audit errors, and `ready_to_freeze_split=false` while human review proceeds.
