# Correct Workflow Root To `/project`

## Goal

Correct the previous hierarchy mistake so the current `/project` directory is the root of this sub-repository's structure and Agent workflow. Remove the mistakenly installed kernel files from the containing `DeepLearning` repository and keep all project plans, logs, experience notes, rules, and entry documentation under `/project`.

## Dirty-State Note

Start state observed from `/project` with `git status --short --branch` resolving to the containing Git checkout:

```text
## agent/refine-deep-learning-paper-notes...origin/agent/refine-deep-learning-paper-notes
 M ../README.md
 M ../notes.md
 M BASELINE_PLAN.md
?? ../AGENTS.md
?? ../docs/
?? ../plan/
?? AGENTS.md
?? DATASET_DOWNLOAD_PLAN.md
?? DATASET_SOURCING.md
?? README.md
?? scripts/
```

`../README.md`, `../AGENTS.md`, `../docs/`, and `../plan/` are changes created by the mistaken hierarchy adoption and are owned only for restoration/removal. `../notes.md`, `BASELINE_PLAN.md`, dataset documents, and `scripts/` are existing user/project work and remain read-only.

## Owner

- Target owner: Codex correcting its previous hierarchy error for the user.

## Owned Files

- `AGENTS.md`
- `README.md`
- `.gitignore`
- `plan/README.md`
- `plan/target-plan.template.md`
- `plan/log.md`
- `plan/2026-07-14-correct-workflow-root/plan.md`
- `docs/experience/README.md`
- `docs/experience/lesson.template.md`
- `../README.md` only to remove the mistakenly added project/kernel section
- `../AGENTS.md` only to delete the mistakenly installed root rules
- `../plan/` only to delete the mistakenly installed kernel files
- `../docs/experience/` only to delete the mistakenly installed kernel files

## Read-Only Files

- `../notes.md`
- `BASELINE_PLAN.md`
- `DATASET_DOWNLOAD_PLAN.md`
- `DATASET_SOURCING.md`
- `scripts/`
- `References/`
- Every other path in the containing course repository

## Shared Dependencies

- Workflow specification: `https://github.com/chenzc24/agent-workflow-kernel`
- Project architecture contract: `BASELINE_PLAN.md`
- The containing Git checkout remains unchanged; this target relocates project management boundaries and does not initialize a nested `.git` or invent a remote.

## Expected Work

1. Install the kernel templates and local workflow directly under `/project`.
2. Rewrite `AGENTS.md` and `README.md` so all paths and commands are relative to `/project`.
3. Add a project-local `.gitignore` suitable for datasets, weights, training outputs, secrets, and local environments.
4. Restore the containing repository README and remove the mistakenly added containing-repository kernel files.
5. Validate that all workflow files are under `/project`, no parent kernel files remain, existing project work is unchanged, and no nested `.git` was created.
6. Record the correction factually in `/project/plan/log.md`.

## Validation

- Scan target-owned Markdown files for trailing whitespace and balanced fences.
- Confirm required local links exist.
- Confirm `../AGENTS.md`, `../plan/`, and the mistakenly created `../docs/experience/` files no longer exist.
- Confirm the containing `../README.md` has no Agent workflow section added by the mistaken target.
- Run `git diff --check -- ../README.md` for the restored tracked parent file.
- Run `git diff --check` and record any pre-existing read-only failures separately.
- Run `git status --short --branch` and verify no files were staged, committed, or pushed.

## Validation Results

- All 9 target-owned project-root workflow paths exist. Their Markdown files have no trailing whitespace or unbalanced fenced code blocks, and all 5 checked project entry links resolve.
- No nested `.git` was created.
- The mistakenly created parent `../AGENTS.md`, `../plan/`, and `../docs/experience/` paths no longer exist.
- `git diff --quiet -- ../README.md` returned 0, confirming the containing repository README was restored exactly; its scoped `git diff --check` also passed.
- `git check-ignore -v --no-index` confirmed the project `.gitignore` excludes representative model weights, raw data, and generated demo video paths.
- Full-worktree `git diff --check` was run and returned exit 2 only for existing read-only whitespace in `../notes.md` at lines 265, 286, 310, and 319, plus `BASELINE_PLAN.md:3`. These paths remain outside this correction target's edit scope.
- `git status --short --branch` shows only existing project/user work plus the corrected `/project` workflow files; nothing was staged, committed, or pushed.

## Experience Signal (for human review)

The user corrected an incorrect repository-boundary assumption before implementation work began. Whether that should become a reusable lesson remains a human decision.

## Commit Intent

Do not commit or push. Leave the corrected project-root workflow ready for user review.
