# Split Formal Baseline And Advanced Plans

## Goal

Replace the obsolete use of “Baseline” for the DeskMate advanced demo with two
coherent delivery plans:

1. a deadline-first plan for the official five-breed cat-census Baseline due
   before the 17 July 2026 evaluation; and
2. a later DeskMate Advanced plan that deliberately reuses the Baseline's
   camera, inference, model packaging, UI, logging, and robot-integration
   infrastructure.

## Dirty-State Note

The project worktree was clean on `main` at `4965cb9` before this target.

## Owned Files

- `BASELINE_PLAN.md` — rewrite around the official cat-classification task.
- `ADVANCED_PLAN.md` — preserve and relabel the existing DeskMate plan, with a
  Baseline-reuse contract and explicit post-Baseline start gate.
- `DATASET_SOURCING.md` -> `ADVANCED_DATASET_SOURCING.md` — clarify that the
  six-class desk-object dataset belongs only to Advanced.
- `DATASET_DOWNLOAD_PLAN.md` -> `ADVANCED_DATASET_DOWNLOAD_PLAN.md` — same
  phase clarification.
- `README.md` — expose the two-phase roadmap and correct entry links.
- `AGENTS.md` — replace the obsolete single-plan architecture contract with
  phase-specific sources of truth.
- `plan/log.md` — record factual validation results.
- This target plan.

## Read-Only Files

- `References/The requirement/**` — authoritative assignment evidence.
- `References/The previous works/**` — presentation references only.
- `scripts/data/download_dataset_sources.ps1` — existing Advanced acquisition tool;
  no behavior change is needed for this documentation target.
- All prior target plans and experience notes.

## Requirements And Dependencies

- Formal sources:
  - `References/The requirement/Assignment announcement.md`
  - `References/The requirement/Baseline SOP.md`
  - `References/The requirement/SWS3009A_Assg.md`
  - `References/The requirement/SWS3009A_AssgAnsBk.md`
- Hardware: one RTX 4070 development laptop, the robot camera/video stream,
  remotely controlled chassis, and console or UI visible to evaluators.
- Baseline task: classify Ragdoll, Singapura, Persian, Sphynx, and Pallas cat;
  use more than 1,000 balanced images where practical; split 85% train and 15%
  validation; print the predicted species; find eight images and return within
  15 minutes.
- Baseline report: architecture justification, per-class image counts, training
  and validation accuracy, and overfitting/underfitting analysis.

## Expected Work

- Make the formal Baseline the only P0 work until it passes an integrated
  recorded-video and robot-stream rehearsal.
- Select one small transfer-learning classifier and one explicit fallback;
  avoid the Advanced multi-expert stack on the Baseline critical path.
- Define a stable inference boundary so the Advanced project can replace the
  classifier without rewriting capture, preprocessing, overlay, telemetry, or
  robot networking.
- Preserve the detailed DeskMate design as Advanced scope rather than deleting
  it.

## Validation

- Cross-check every hard Baseline requirement against all four requirement
  transcriptions.
- Check that Baseline and Advanced model IDs, priorities, dates, and entry links
  are internally consistent.
- Confirm the old desk-object dataset documents are referenced only as Advanced.
- Confirm all referenced local paths exist.
- Run Markdown heading/link checks, `git diff --check`, and
  `git status --short --branch`.

## Validation Results

- Cross-checked the Baseline plan against the announcement, SOP, assignment,
  and answer-book transcriptions for five classes, image volume, 85/15 split,
  transfer learning, visible species output, eight targets, remote control,
  15-minute run, attendance, evaluation date, and report deadline.
- Verified seven owned Markdown files have balanced code fences and all 14
  relative Markdown links resolve to local files or directories.
- Verified the original Advanced plan retained all 17 numbered product sections
  and grew from 1,006 to 1,036 lines after adding the phase/reuse contract.
- Confirmed active entry documents contain no references to the obsolete
  `DATASET_SOURCING.md` or `DATASET_DOWNLOAD_PLAN.md` names.
- `git diff --check` passed. Final status contains only the files declared by
  this target; no real robot test was claimed for this documentation change.

## Real Robot Motion

None. This target changes documentation only. Later integration follows the
remote-control and safety procedures in the Baseline plan.

## Commit Intent

Do not commit or push automatically. Leave the bounded documentation changes
for human review unless the user explicitly requests publication.
