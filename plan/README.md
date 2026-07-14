# Plan Directory

The `plan/` directory stores implementation intent and factual maintenance
history for this project repository. It exists so Agents do not make unbounded,
unowned, or unverifiable changes.

## Target Plans

Create a target plan before editing tracked project files.

Default path:

```text
plan/<YYYY-MM-DD-target-name>/plan.md
```

Example:

```text
plan/2026-07-15-scaffold-multi-expert-runtime/plan.md
```

Start from `plan/target-plan.template.md`. Every plan identifies the goal,
owner, dirty-state decision, owned and read-only paths, shared dependencies,
implementation work, validation, and commit policy.

## Dirty Worktree Handling

A dirty worktree does not automatically block unrelated work. Continue only
when dirty paths do not overlap the target's owned paths or alter a shared
contract the target depends on. Record the decision in the target plan. Stop
and coordinate when ownership is unclear or overlap exists.

When this project is physically located inside another checkout, parent dirty
paths remain outside project ownership. Do not stage or modify them unless a
correction target explicitly names them.

## Maintenance Log

`plan/log.md` records accepted factual project maintenance history. Each entry
contains:

- date and target;
- changed areas;
- validation performed;
- commit status.

Plans explain intent before work. Logs explain factual outcomes after work. Git
records actual repository state.

## Experience Extraction

Experience extraction is a human decision, not an automatic close-out step.
When a human requests it, an Agent may draft a candidate under
`docs/experience/` and cite relevant plans, logs, commits, reviews, validation
reports, or failed attempts.

Completed plans may be archived after their outcome is logged. Blocked,
unresolved, or superseded plans remain visible until a human resolves their
status.
