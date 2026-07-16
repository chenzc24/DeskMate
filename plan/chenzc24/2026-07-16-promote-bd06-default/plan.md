# Promote BD06 + M9 as the default baseline

## Outcome and owned paths

Make the canonical target-five inference config resolve to frozen BD06 and M9,
publish both required weights in the same GitHub Release, and retain BD05+M9
as the explicit rollback.

Owned tracked paths:

- `configs/baseline_inference_target5_robot.toml`
- `models/frozen/baseline-bd06-m09.toml`
- `models/frozen/baseline-bd06-m09.json`
- `models/manifest.yaml`
- `docs/evaluation/BASELINE_FIVE_BREED_DETECTOR_20260716.md`
- `tests/test_bd06_default_config.py`
- this plan

## Dirty paths left read-only

Preserve the existing `.gitignore`, `plan/log.md`, presentation showcase, and
detector handoff worktree changes.

## Dependencies

- frozen BD06 and M9 weights with their pinned SHA-256 values;
- GitHub Release `bd06-20260716` in `chenzc24/DeskMate`.

## Validation and robot motion

Parse all TOML/JSON/YAML records, verify default/frozen config agreement,
verify both local checkpoint hashes and both Release assets, run the full test
suite, and check Git diffs. No robot connection or motion is involved.

## Commit intent

Commit only the owned paths directly to `main` and push, as explicitly
requested by the repository owner.
