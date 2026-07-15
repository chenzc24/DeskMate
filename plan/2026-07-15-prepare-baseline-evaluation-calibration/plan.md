# Prepare Baseline Evaluation And Calibration

## Outcome

Prepare deterministic, framework-neutral evaluation and temperature-calibration
tooling so the first legitimate fine-tuned checkpoint can be assessed without
ad-hoc notebooks or split leakage. This is later-phase preparation permitted by
the Baseline plan; it does not freeze thresholds or claim model performance.

## Owned Files And Directories

- `configs/baseline_evaluation.toml`
- new evaluation modules under `src/deskmate_baseline/`
- evaluation scripts under `scripts/`
- targeted tests under `tests/`
- `docs/evaluation/BASELINE_EVALUATION_TOOLING_READINESS.md`
- `docs/evaluation/BASELINE_EVALUATION_TOOLING_READINESS.json`
- `plan/log.md`
- this target plan
- ignored prediction manifests and generated evaluation artifacts

## Read-Only And Deferred Paths

- requirements and high-level plans
- Phase 0/1 data and human-review evidence
- frozen training/inference configuration and model manifest
- robot calibration/final images and stream configuration
- parent workspace

## Contracts

- Input is a CSV prediction manifest with image ID, frozen split, true label,
  canonical six probabilities, model/checkpoint ID, and dataset/checkpoint
  checksums.
- `val_select` chooses epoch/seed/architecture; `val_cal` fits temperature and
  thresholds. The tool refuses mixed roles or missing provenance.
- Temperature fitting uses only `val_cal`; final/robot evidence cannot be used
  as a fitting input.
- Report target-only accuracy/macro-F1/per-class recall separately from
  six-class accuracy and `not_target` rejection.
- NLL and ECE are reported before and after calibration. Temperature is fitted
  deterministically and is not written to release config by this target.
- Empty classes, malformed probabilities, duplicate image IDs, unknown labels,
  probability sums, mixed checkpoint/dataset hashes, and split leakage fail
  closed.

## Work

1. Define and validate the portable prediction-manifest schema.
2. Implement confusion matrix, target-only accuracy, macro-F1, class recall,
   negative rejection, NLL, and ECE.
3. Implement deterministic scalar temperature fitting on `val_cal`.
4. Add synthetic fixtures proving role separation, calibration improvement,
   and all error cases.
5. Produce readiness evidence without evaluating the untrained base model as a
   Baseline checkpoint.

## Validation

- compile and run all tests in default and pinned environments
- parse TOML/JSON and validate deterministic repeat output
- verify temperature fitting never reads `val_select`, robot calibration, or final
- verify calibrated probabilities remain normalized and canonical
- verify metric values against hand-computed fixtures
- confirm B0/B1 status is unchanged and no official performance report exists
- confirm requirements unchanged; run diff/status checks

## Robot Motion

None.

## Commit Intent

No branch, commit, push, or PR unless explicitly requested.

## Validation Results

Completed deterministic evaluation and calibration preparation without
evaluating or calibrating an official checkpoint.

- Added a strict portable prediction manifest with canonical six-probability
  order and required model, dataset, checkpoint, group, image, and split
  provenance.
- Added six-class and target-only metrics, confusion matrix, per-class recall,
  negative rejection, NLL, ECE, and deterministic scalar temperature fitting.
- Temperature fitting accepts `val_cal` only. Mixed split roles, duplicate IDs,
  malformed probabilities, and mixed provenance fail closed.
- A six-row synthetic fixture exercised the complete CLI. It fitted temperature
  1.65 and reduced fixture NLL from 1.37425 to 1.17300 while preserving
  normalized probabilities. These values are calculation evidence only.
- Both Python environments pass all 52 tests. TOML/JSON parsing, four tracked
  checksums, repeat fixture evaluation, B0/B1 audits, requirement immutability,
  and `git diff --check` pass.

No real checkpoint metrics, temperature/threshold freeze, split, training,
robot connection, motion, branch, commit, push, or PR was produced.
