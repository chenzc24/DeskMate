# Reorganize code layout

## Outcome and owned paths

Restructure `src/deskmate_baseline/` into responsibility-based subpackages
without changing the installed package name or breaking existing imports and
script commands. Add a documented destination for later migration of the flat
`scripts/` implementations.

Owned paths:

- `src/deskmate_baseline/`
- import-only compatibility updates in `tests/`
- `pyproject.toml` only if package discovery or entry points require it
- this target plan and one factual completion entry in `plan/log.md`

## Read-only paths

- `data/`, `models/`, `runs/`, `artifacts/`, and `References/`
- all configs and evaluation evidence
- frozen BD05 and M9 assets

## Dependencies

No new external data, models, services, or hardware. Existing Python tooling
only.

## Validation and robot motion

- preserve legacy `deskmate_baseline.<module>` imports through compatibility
  shims;
- verify new responsibility-based import paths;
- compile all Python files and run `python -m pytest -q`;
- run `git diff --check` and inspect repository status.

No robot motion is involved.

## Commit intent

Do not commit or push unless the user explicitly asks after reviewing the
refactor.
