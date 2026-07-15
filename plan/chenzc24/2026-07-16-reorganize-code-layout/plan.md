# Reorganize code layout

## Outcome and owned paths

Restructure `src/deskmate_baseline/` into responsibility-based subpackages,
then finish the cleanup by removing root-level compatibility modules and
grouping executable scripts by workflow. Update all repository-owned imports
and command references to their canonical locations.

Owned paths:

- `src/deskmate_baseline/`
- `scripts/`, tests, and documentation (including `data/README.md`) that
  directly reference moved commands
- `pyproject.toml` only if package discovery or entry points require it
- this target plan and one factual completion entry in `plan/log.md`

## Read-only paths

- dataset contents under `data/`, plus `models/`, `runs/`, `artifacts/`, and
  `References/`
- all configs and evaluation evidence
- frozen BD05 and M9 assets

## Dependencies

No new external data, models, services, or hardware. Existing Python tooling
only.

## Validation and robot motion

- verify responsibility-based import paths and grouped script modules;
- keep the `scripts/` root limited to package metadata and a layout README;
- compile all Python files and run `python -m pytest -q`;
- run `git diff --check` and inspect repository status.

No robot motion is involved.

## Commit intent

Do not commit or push unless the user explicitly asks after reviewing the
refactor.
