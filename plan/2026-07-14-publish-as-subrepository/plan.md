# Publish DeskMate as a subrepository

## Goal

Publish the current `/project` tree as the independent private GitHub repository
`chenzc24/DeskMate`, then replace the parent repository's tracked `project/`
contents with a Git submodule pointing to that repository.

## Repository state before work

- Parent repository: `chenzc24/DeepLearning`
- Parent branch: `agent/refine-deep-learning-paper-notes`
- Parent dirty state:
  - `notes.md` is modified and unrelated to this target.
  - `project/BASELINE_PLAN.md` is modified.
  - The remaining current project workflow, dataset, and script files are untracked.
- `chenzc24/DeskMate` does not exist yet.

## Ownership

Writable for this target:

- The complete current `project/` tree for its initial child-repository commit.
- Parent `.gitmodules`.
- Parent Git index entry for `project`, converting tracked files to a gitlink.

Read-only/out of scope:

- Parent `notes.md` and every other parent-repository path.

## Steps

- [x] Create private GitHub repository `chenzc24/DeskMate`.
- [x] Initialize `project/` as an independent repository on branch `main`.
- [ ] Validate, commit, and push the complete current project tree.
- [ ] Convert parent `project/` to a Git submodule and absorb its Git directory.
- [ ] Verify that the parent stages only `.gitmodules` and the `project` gitlink.
- [ ] Commit and push the parent branch.

## Validation

- Child: `git status --short`, `git diff --cached --check`, and remote/branch checks.
- GitHub: verify `chenzc24/DeskMate` visibility and default branch.
- Parent: verify `git ls-files --stage project` reports mode `160000`.
- Parent: verify `notes.md` remains modified but unstaged.
- Parent: `git diff --cached --check` before commit.

## Commit intent

- Child commit: `Initialize DeskMate subrepository`
- Parent commit: `Track DeskMate as submodule`
- Push the child `main` branch and the current parent feature branch.
- Do not open a pull request unless explicitly requested.
