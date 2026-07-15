# Balanced-300 Classifier Ablation

Status: **development experiment; not a release metric**.

## Dataset

Built from the user's current detector-view handoff after removing other-cat
negative images. Target classes were deterministically downsampled to about
300 unique parents with the existing 85/10/5 split. Singapura had only 298
available unique images and was retained at 298 rather than duplicated.

| Class | Train | Val | Val-cal | Total |
| --- | ---: | ---: | ---: | ---: |
| Ragdoll | 255 | 30 | 15 | 300 |
| Singapura | 253 | 30 | 15 | 298 |
| Persian | 255 | 30 | 15 | 300 |
| Sphynx | 255 | 30 | 15 | 300 |
| Pallas | 255 | 30 | 15 | 300 |
| not_target | 321 | 37 | 19 | 377 |

No other-cat files were present in the generated `not_target` training
directory. The original handoff and frozen checkpoint were not modified.

## Training

- Model: Ultralytics `yolo26s-cls.pt`, same augmentation as the provisional
  baseline
- Hardware: NVIDIA RTX 4070 Laptop GPU
- Best epoch: 15 of 27 completed epochs
- Best training validation top-1/top-5: 96.79% / 100%
- Checkpoint: ignored `runs/baseline_balanced300/.../weights/best.pt`

## Same balanced validation comparison

| Model | Overall top-1 | Singapura recall | Pallas recall | not_target recall |
| --- | ---: | ---: | ---: | ---: |
| Frozen provisional | 97.33% | 96.67% | 100% | 94.59% |
| Balanced-300 | 96.79% | 90.00% | 100% | 97.30% |

The first run does not yet show a benefit for Singapura or Pallas. It improves
negative rejection on this balanced validation set, but Singapura recall is
lower. Robot-camera domain evaluation remains a separate required comparison;
this result alone cannot establish that imbalance is the dominant cause.

## Robot-camera still comparison

The same nine saved routed crops from `artifacts/robot_camera_eval/batch_20260715_1237`
were classified with the detector and route held fixed. The printed labels are
human-read descriptive labels, not a held-out release set.

| Classifier | Descriptive correct | Notes |
| --- | ---: | --- |
| Frozen provisional | 6/9 (66.7%) | Pallas stills were both predicted Persian |
| Balanced-300 | 6/9 (66.7%) | One Pallas changed to correct Pallas; two other frames regressed to `not_target` |

Balanced-300 changed frames 4, 8, and 9: Persian became `not_target`, one
Pallas became correct Pallas, and the other Pallas became `not_target`. The
detector, route, and input crops were identical, so these changes are from the
classifier only. This run does not show a net robot-camera accuracy gain.
