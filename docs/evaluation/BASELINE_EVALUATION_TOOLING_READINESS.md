# Baseline Evaluation And Calibration Tooling Readiness

Status: **tooling ready; real checkpoint predictions pending**.

The model-selection and calibration metrics can now be generated from one
portable prediction manifest without using notebooks or framework-native
objects. No metric in this report is an official model result because a
fine-tuned checkpoint and frozen split do not yet exist.

## Supported Evidence

- Canonical six-class confusion matrix and accuracy.
- Five-target-only accuracy, macro-F1, and per-class recall.
- Separate `not_target` rejection rate.
- Negative log-likelihood and expected calibration error.
- Deterministic scalar temperature fitting over a frozen search range.
- Model ID, dataset checksum, checkpoint checksum, source group, image ID, and
  split-role validation on every prediction row.

## Leakage Controls

`val_select` is reserved for epoch, seed, and architecture selection.
`val_cal` is the only accepted input for temperature fitting. Robot calibration
and one-time robot final results are distinct roles. Mixed-role manifests,
duplicate IDs, malformed probability vectors, unknown classes, and mixed
dataset/checkpoint provenance fail closed.

The tool does not write temperature or thresholds into the release
configuration. Those values remain provisional until real `val_cal` and robot
calibration evidence exists.

## Deterministic Fixture Smoke

A six-row synthetic `val_cal` fixture exercised the complete CLI. It fitted
temperature `1.65` and reduced fixture NLL from `1.37425` to `1.17300`; the
probabilities remained normalized. These numbers validate calculations only
and are not model performance.

Both Python environments pass all 52 tests. B0 still lacks the two deferred
robot inputs, B1 still has 2,321 pending reviews, and no training, calibration
freeze, final evaluation, robot connection, or motion occurred.
