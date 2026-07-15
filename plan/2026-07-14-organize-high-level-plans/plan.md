# Organize High-Level Plans Under `docs/plans`

## Goal

Move the four high-level Baseline, Advanced, and Advanced-data planning documents
out of the repository root into one discoverable `docs/plans/` directory. Keep
root `AGENTS.md` active as repository policy, make it point to those plans as
design principles, and preserve `References/The requirement/` as the
authoritative original requirement material.

## Dirty-State Note

The worktree already contains the complete, uncommitted output of the preceding
formal-Baseline/Advanced split target. Those changes are intentionally in scope
for path updates only; their technical content remains unchanged.

## Owned Files

- `BASELINE_PLAN.md` -> `docs/plans/BASELINE_PLAN.md`
- `ADVANCED_PLAN.md` -> `docs/plans/ADVANCED_PLAN.md`
- `ADVANCED_DATASET_SOURCING.md` ->
  `docs/plans/ADVANCED_DATASET_SOURCING.md`
- `ADVANCED_DATASET_DOWNLOAD_PLAN.md` ->
  `docs/plans/ADVANCED_DATASET_DOWNLOAD_PLAN.md`
- `docs/plans/README.md` — plan index and precedence statement.
- `AGENTS.md` — root policy references and phase principles.
- `README.md` — repository entry links.
- `plan/log.md` — factual outcome.
- This target plan.

## Read-Only Files

- `References/The requirement/**` — authoritative assignment originals and
  faithful Markdown transcriptions; no content change.
- `References/The previous works/**`.
- Source scripts, prior target plans, and experience notes.

## Expected Work

- Preserve root `AGENTS.md`; moving it would stop repository-wide rule discovery.
- Move only the four high-level plan/data documents into `docs/plans/`.
- Repair cross-plan links and their relative links back to the requirement
  originals.
- Declare precedence: formal requirement originals first, Baseline principles
  second for current P0, Advanced principles only after Baseline Gate B4.

## Validation

- Confirm all four root plan paths are absent and all five `docs/plans/` entry
  files exist.
- Resolve every relative Markdown link in active documentation.
- Confirm `AGENTS.md` stays at repository root and names the phase principles and
  authoritative requirement directory.
- Confirm plan content, section counts, dates, model IDs, and gates are unchanged
  except for path/index wording.
- Run whitespace/fence checks, `git diff --check`, and final status review.

## Validation Results

- Confirmed the four high-level documents are absent from the repository root
  and the four moved documents plus `docs/plans/README.md` exist.
- Resolved 20 active relative Markdown links, including links from the moved
  Baseline plan back to all four requirement transcriptions.
- Confirmed root `AGENTS.md` names all four plan principles, states that
  `References/The requirement/` outranks project-authored plans, and retains the
  Baseline-to-Advanced Gate B4 order.
- Confirmed the Advanced plan still contains its phase section plus all 17
  original numbered product sections.
- Whitespace, code-fence, `git diff --check`, and final scope checks passed.

## Real Robot Motion

None. Documentation organization only.

## Commit Intent

Do not commit or push automatically; leave the combined bounded changes for
human review.
