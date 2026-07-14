# Maintenance Log

This log records accepted factual maintenance history for this project. Keep
reusable lessons in `docs/experience/`, not in this log.

Use concise entries:

```text
## YYYY-MM-DD - Target title

- Target: what the work set out to do.
- Changed areas: files, directories, or subsystems changed.
- Validation: commands or review performed.
- Commit status: committed, ready to commit, not committed, or blocked.
```

## 2026-07-14 - Correct Workflow Root To `/project`

- Target: correct the repository-boundary mistake so the current `/project` directory is the root for Agent rules, target plans, factual logs, experience notes, project entry documentation, and artifact policy.
- Changed areas: installed `AGENTS.md`, `README.md`, `.gitignore`, `plan/`, and `docs/experience/` under `/project`; removed the mistakenly installed parent kernel files; restored the containing repository README.
- Validation: checked all 9 owned paths, Markdown whitespace/fences, 5 local entry links, absence of parent kernel residue and nested `.git`, exact restoration of the parent README, and representative ignore rules. Full `git diff --check` was run and reported only pre-existing read-only whitespace in `../notes.md` and `BASELINE_PLAN.md`.
- Commit status: not committed; ready for user review. No file was staged or pushed.

## 2026-07-14 - Publish DeskMate As A Subrepository

- Target: publish the current `/project` tree as private repository `chenzc24/DeskMate`, then track it from `chenzc24/DeepLearning` as the `project` Git submodule.
- Changed areas: initialized the child repository, added its GitHub remote, prepared the complete project tree for the initial commit, and reserved the parent `.gitmodules` and `project` gitlink as the only parent-repository changes.
- Validation: reviewed the staged child file list and diff summary, ran `git diff --cached --check`, and scanned staged text files for common private-key and access-token signatures.
- Commit status: child repository ready to commit as `Initialize DeskMate subrepository`; parent conversion will follow the successful child push. No pull request requested.
