# Singapura/Pallas Classifier Hardening

Status: **single-model development candidate selected; not release-admitted**.

The selected checkpoint is one classifier, not a runtime ensemble:

- model: `B-M01-SP-HARDENED-CANDIDATE`;
- path: `runs/baseline_classifier_hardening/soups/b50_p50.pt`;
- SHA-256: `0d598ec33773e82b147380c9fa866c71482fe42800dae1086fb63b90935b3296`;
- construction: deterministic 50/50 weight average of the balanced one-view and
  train-only printed-page candidates.

## Data And Training

Both candidates start from the same pinned ImageNet `yolo26s-cls.pt`, use the
canonical six-output order, and use no robot-camera image for training. Each
variant contains 573 training views per class and retains the frozen 280
`val_select` plus 139 `val_cal` parents. The printed-page augmentation is
label-free and is generated only from train parents for Singapura and Pallas.

The dataset manifest reproduced byte-for-byte across two independent builds:
`1dd6e54b36fa93299639c8b2316fb8841ff61516ef7dbe920658deac6ca3b2ba`.
The final weight-soup checkpoint also reproduced with the SHA-256 above.

## Same-ROI Comparison

Every model received the identical output from the hardened detector/crop/
fallback route.

| Metric | Current B-M01 | Candidate | Change |
|---|---:|---:|---:|
| Validation correct | 399/419 | 403/419 | +4 |
| Validation macro F1 | 0.9534 | 0.9656 | +0.0122 |
| Singapura validation | 43/45 | 42/45 | -1 |
| Pallas validation | 44/45 | 45/45 | +1 |
| Robot stills | 7/9 | 8/9 | +1 |
| Robot Singapura | 1/1 | 1/1 | unchanged |
| Robot Pallas | 0/2 | 2/2 | +2 |
| Classifier mean latency | 11.64 ms | 11.54 ms | effectively unchanged |
| Classifier P95 latency | 20.97 ms | 20.29 ms | effectively unchanged |

Pallas is materially improved in the available diagnostics. Singapura is not
yet proven improved: its sole robot still remains correct, while frozen
validation loses one correct example. The candidate also changes one robot
Persian still from correct to `not_target`. Therefore the checkpoint is wired
only as a disabled development candidate and does not replace the current
release model automatically.

## Next Admission Gate

Collect a new, session-grouped robot-camera set containing multiple unseen
Singapura, Pallas, and Persian base images at relevant distances and lighting.
Select thresholds without this set, then compare current and candidate once on
that frozen set. Admit the candidate only if the Pallas gain persists without a
material Singapura, Persian, or rejection regression.

Machine-readable evidence is in
`docs/evaluation/BASELINE_CLASSIFIER_HARDENING.json`; detailed per-image output
and the visual robot comparison remain generated artifacts under
`data/downloads/baseline_classifier_hardening/evaluation/`.
