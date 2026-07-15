# Adopt User-Scoped Plan Layout

## Outcome

Make concurrent human/agent collaboration easier to navigate by changing the
default target-plan path from a flat date-prefixed directory to a user-scoped
layout:

```text
plan/<user>/<YYYY-MM-DD-target-name>/plan.md
```

Keep already-published flat plans in place as history; new and still-uncommitted
plans use the user-scoped layout.

## Owner

- Target owner: `chenzc24`
- Execution agent: `Codex`

## Owned Files

- `AGENTS.md`
- `plan/README.md`
- `plan/chenzc24/2026-07-15-adopt-user-scoped-plan-layout/plan.md`

## Read-Only Files And Directories

- all existing published target plans
- the active human-screened intake implementation and evidence files
- `References/The requirement/`
- all model, dataset, robot, source, test, and runtime artifact paths

## Dependencies And Decisions

- Use the collaborator's stable GitHub/Git username as `<user>`; this target
  uses `chenzc24` from the configured Git identity.
- Keep target dates and names below the user directory for chronological
  browsing and bounded ownership.
- Do not bulk-rename already-published plans, because doing so would add noisy
  history and break existing links without improving their factual record.

## Validation

- Confirm `AGENTS.md` and `plan/README.md` describe the same default path.
- Confirm examples resolve to real or explicitly future paths.
- Run `git diff --check` and scoped status review.

Documentation-only change; recorded-video validation and robot motion are not
applicable.

## Commit Intent

The user explicitly requested the clearer user-scoped convention during the
active publish workflow. Commit this convention separately before the intake
target and push both to `main`; do not open a pull request.

## Validation Results

- `AGENTS.md` and `plan/README.md` use the identical default path
  `plan/<user>/<YYYY-MM-DD-target-name>/plan.md`.
- The example uses configured GitHub/Git username `chenzc24`; existing
  published flat plans are explicitly retained as historical records.
- `git diff --check` and scoped status review passed. No runtime, dataset,
  model, robot, or generated-artifact path was changed.
