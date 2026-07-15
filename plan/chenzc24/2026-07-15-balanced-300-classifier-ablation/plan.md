# Train Balanced-300 Classifier Ablation

## Goal

Test whether the low Singapura/Pallas robot recognition is partly caused by
class-count imbalance. Build a deterministic one-view classifier dataset with
approximately 300 images per target class, while keeping the existing frozen
dataset and checkpoint unchanged.

## Owned files

- `scripts/data/build_balanced_300_ablation.py`
- `configs/baseline_training_balanced300.toml`
- generated ignored `data/downloads/baseline_balanced300/`
- generated ignored `runs/baseline_balanced300/`
- this plan and its future evaluation record

## Source and policy

Source is the current handoff one-view dataset after the user's removal of
other-cat `not_target` images. Target classes are sampled to 300 total using
the existing 85/10/5 split: 255 train, 30 model-selection validation, and 15
calibration. All available `not_target` images are retained. Sampling is
deterministic and does not duplicate files or cross source groups.

## Validation

- Assert exact target counts and no `other_cat_breed` files in `not_target`.
- Run the complete test suite and the new dataset audit.
- Train one RTX 4070 development checkpoint with the same augmentation and
  Ultralytics model as the frozen baseline.
- Compare per-class metrics, `not_target` rejection, and the same robot-camera
  batch against the frozen checkpoint.

## Commit intent

No commit or push unless explicitly requested after the ablation is reviewed.

## Initial result

The dataset build and one RTX 4070 training run completed. The five target
classes are 300/298/300/300/300 images; `not_target` is 377 images with no
other-cat files. The best epoch was 15/27 with 96.79% validation top-1. On the
same balanced validation set, the frozen provisional model scored 97.33%,
while the balanced model scored 96.79%; Singapura recall was 90.0% versus
96.67%, Pallas recall was 100% for both, and `not_target` recall improved from
94.59% to 97.30%. On the same nine routed robot-camera crops, both models
scored 6/9 (66.7%) by the human-read printed labels; Balanced-300 corrected
one Pallas but changed a Persian and the other Pallas to `not_target`. No net
robot-camera gain was observed.
