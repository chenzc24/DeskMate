# Ragdoll supplementary review and M10 experiment — 2026-07-15

## Outcome

M10 is rejected. Keep M9 as the classifier and `BD05 + M9` as the default
pipeline candidate.

## Data change

- Ragdoll originals before supplementary review: 521.
- Ragdoll originals after supplementary review: 459.
- Additional Ragdoll deletions: 62.
- Total deletions relative to the original 523 Ragdoll images: 64.
- The existing augmentation families and seed `20260715` were retained.
- Ragdoll was augmented from 459 originals to 1,200 training views.
- The 24-image diagnostic source overlap remained zero.

## Training

M10 was initialized from `models/yolo26s-cls.pt`, not M9. It completed 30
epochs with early stopping and reached 97.47% validation top-1, equal to M9.

- Checkpoint: `runs/baseline_target5_manual_curated_ragdoll_reviewed_augmented/b-m10-target5-ragdoll-reviewed-aug-seed-20260715/weights/best.pt`
- SHA-256: `8dc53456e6e15b49295c8cab06f6a166dc4d4e99e8bd5288a621e54f87190cab`

## Robot full-pipeline regression

| Combination | 24 images | 24 groups | 11 robot images | Combined |
|---|---:|---:|---:|---:|
| BD04 + M9 | 23/24 | 8/8 | 9/11 | 32/35 |
| BD05 + M9 | 22/24 | 8/8 | 10/11 | 32/35 |
| BD04 + M10 | 18/24 | 6/8 | 9/11 | 27/35 |
| BD05 + M10 | 18/24 | 6/8 | 10/11 | 28/35 |

With BD05, M10 missed four Ragdoll frames in the 24-image set and one Ragdoll
frame in the 11-image set. `Ragdoll_01` remained Sphynx and became more
confident: 70.9% with M10 versus 57.1% with M9 on the BD05 crop.

The supplementary deletions therefore removed useful robot-domain variation or
shifted the learned Ragdoll boundary unfavorably. Conventional validation did
not expose this regression. The preserved M9 source dataset and checkpoint must
remain the active assets; M10 is negative experiment evidence only.
