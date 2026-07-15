# High-Level Project Plans

This directory contains product and data principles, not the original course
requirements and not short-lived implementation target plans.

## Authority And Phase Order

1. [`References/The requirement/`](<../../References/The requirement/>) contains
   the authoritative assignment originals and faithful local transcriptions. If
   a project plan conflicts with those materials, the requirement material wins.
2. [Official Baseline plan](BASELINE_PLAN.md) is the current execution principle
   until the five-breed Cat Census passes Gate B4 and its offline release is
   frozen.
3. [DeskMate Advanced plan](ADVANCED_PLAN.md) becomes active only after that
   Baseline gate. It reuses the proven video, inference, packaging, UI, logging,
   replay, and robot-integration infrastructure.
4. [Advanced dataset sourcing](ADVANCED_DATASET_SOURCING.md) and
   [Advanced dataset download plan](ADVANCED_DATASET_DOWNLOAD_PLAN.md) apply only
   to the post-Baseline desk-object task; they are not cat-dataset instructions.

## Document Types

- High-level principles live here under `docs/plans/`.
- Formal source material stays under `References/The requirement/`.
- Bounded engineering work uses `plan/<YYYY-MM-DD-target-name>/plan.md` and logs
  factual outcomes in `plan/log.md`.
- Repository-wide rules stay in root `AGENTS.md` so Agents discover them before
  editing project files.
