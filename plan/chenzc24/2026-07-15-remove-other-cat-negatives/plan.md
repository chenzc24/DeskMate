# Remove Other-Cat-Breed Negatives From The Baseline Dataset

## Goal

Stop treating other cat breeds as required `not_target` training data. The
baseline rejection set will focus on non-cat scenes and robot-domain
backgrounds relevant to the demo: desks, floors, robots, walls, hands, and
other objects. Existing frozen data and checkpoint artifacts remain intact for
reproducibility; a later dataset rebuild must exclude `other_cat_breed` rows.

## Owned files

- `configs/baseline_sources.toml`
- `configs/baseline_phase1_data.toml`
- `data/README.md`
- this plan

## Read-only / deferred

- Existing manifests, frozen detector views, checkpoints, and validation
  diagnostics; they are not rewritten by this target.
- Historical plans and pilot logs that document the earlier source choice.

## Contract change

The next baseline data freeze must regenerate `not_target` without
`other_cat_breed`. Until that rebuild and retraining are complete, published
metrics remain metrics for the old six-class dataset and must be labelled as
such.

## Validation

- Parse both TOML configurations.
- Confirm no active acquisition category contains `other_cat_breed`.
- Run `git diff --check` and targeted configuration tests if available.

## Commit intent

No commit or push in this target unless explicitly requested after review.
