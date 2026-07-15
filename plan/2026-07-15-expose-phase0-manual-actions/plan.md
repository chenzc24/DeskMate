# Expose Phase 0 Manual Actions

## Outcome

Publish one operator-facing checklist that exposes the remaining human inputs,
clearly separates Gate B0 robot evidence from Gate B1 dataset review, and keeps
both gates fail-closed.

## Owned Paths

- `README.md`
- `docs/evaluation/BASELINE_PHASE0_B0_REPORT.md`
- `docs/evaluation/BASELINE_PHASE0_B0_REPORT.json`
- `docs/evaluation/BASELINE_PHASE0_MANUAL_ACTIONS.md`
- `plan/2026-07-15-expose-phase0-manual-actions/plan.md`
- `plan/log.md`

## Read-Only Existing Paths

- `References/The requirement/`
- `docs/plans/`
- `configs/`
- `src/`, `scripts/`, and `tests/`
- all ignored datasets, model weights, videos, and runtime artifacts
- all unrelated parent-workspace paths

## Dependencies And Boundaries

- The current machine-readable B0 report is authoritative for gate status.
- A Robotics owner must supply the real camera frame and non-secret stream
  contract details.
- Human reviewers must decide image acceptance; the existing Codex visual
  precheck has no acceptance authority.
- This target changes documentation and refreshes generated audit evidence
  only. It does not change models, datasets, inference, fusion, or protocols.

## Validation

- Parse the machine-readable B0 report with a real JSON parser.
- Confirm B0 reports exactly `real_robot_frame` and `robot_stream_contract` as
  failed.
- Run the B1 review auditor and confirm it remains fail-closed while review is
  pending.
- Run both available Python environments' complete test suites.
- Confirm local Markdown links resolve and requirement originals are unchanged.
- Run `git diff --check` and review scoped Git status.
- Recorded-video validation is not applicable to this documentation target;
  the prior fixture replay is not claimed as robot evidence.

## Robot Motion

No real robot motion is involved. Baseline DL remains read-only with respect to
the robot and never issues motor commands.

## Commit Intent

The user explicitly requested a bounded follow-up commit and push to `main`.
Stage only the owned paths above. Do not create a pull request.

## Validation Results

- System Python 3.13: 55 tests passed.
- Training `.venv` Python 3.12: 55 tests passed.
- B0 verifier intentionally exited 3 with status `NOT_PASSED` and exactly
  `real_robot_frame` plus `robot_stream_contract` failed.
- B1 auditor intentionally exited 3 with 2,321 pending, zero accepted, zero
  audit errors, and `ready_to_freeze_split=false`.
- Required local paths exist; requirement originals have no diff.
- JSON parsing and `git diff --check` passed.
