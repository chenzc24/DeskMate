# Manual-curated Baseline retraining — 2026-07-15

## Decision

- Default candidate: `BD05 + M9`.
- Development-set challenger: `BD04 + M9`.
- M9 replaces M8 as the classifier candidate. BD04 remains available because
  the 24-image development set is one frame better with BD04, while BD05 is
  one frame better on the newer 11-image robot-camera set.

Both new models were initialized from the pinned public pretrained weights,
not from an earlier project checkpoint:

- M9: `models/yolo26s-cls.pt` (ImageNet pretrained).
- BD05: `models/yolo26s.pt` (COCO pretrained).

## Manual review and dataset rebuild

Classifier train originals: 2,074 -> 1,973 accepted.

| Class | Before | After | Deleted | Augmented train total |
|---|---:|---:|---:|---:|
| Ragdoll | 523 | 521 | 2 | 1,200 |
| Singapura | 288 | 242 | 46 | 1,200 |
| Persian | 584 | 556 | 28 | 1,200 |
| Sphynx | 410 | 388 | 22 | 1,200 |
| Pallas | 269 | 266 | 3 | 1,200 |

The frozen M8 validation and calibration splits were preserved. The existing
camera augmentation families and seed `20260715` were retained. Exact overlap
with the 24-image diagnostic source manifest was zero.

Detector training retained 565 manually labelled positive images and 315 of
318 reviewed backgrounds. The BD04 screen/print homography logic was retained:
565 synthetic screen/print positives and 160 blank-panel hard negatives, for
1,605 training images total.

## Training results

### M9 classifier

- Run: `runs/baseline_target5_manual_curated_augmented/b-m09-target5-manual-curated-aug-seed-20260715`
- Best epoch: 20 (one-based), 29 epochs completed with early stopping.
- Validation top-1: 97.47%; M8 was 97.05%.
- Best checkpoint SHA-256: `d8eb66e7ee102e20efc15b385a4c73781596b38a790356510cb04caaf91cafc1`.

### BD05 detector

- Run: `runs/detector_tuner/bd05-manual-curated-screenprint-from-pretrained-seed-20260715`
- Best epoch: 14 (one-based), 24 epochs completed with early stopping.
- Validation: precision 97.3%, recall 97.1%, mAP50 98.4%, mAP50-95 69.3%.
- Best checkpoint SHA-256: `b290f57f3534b60a59b5f1d281b209ff773b8acab4b20a90458be9af51fbe503`.

## Full-pipeline comparison

Frozen routing: confidence 0.25, minimum area 2%, padding 25%, centre fallback
80%.

| Combination | 24 images | 11 robot images | Combined |
|---|---:|---:|---:|
| BD04 + M8 | 20/24 | 9/11 | 29/35 |
| BD04 + M9 | 23/24 | 9/11 | 32/35 |
| BD05 + M8 | 20/24 | 10/11 | 30/35 |
| BD05 + M9 | 22/24 | 10/11 | 32/35 |

BD05 independent detector regression:

- Held-out Sphynx/Pallas ground-truth boxes: 49/49 images matched at IoU >= 0.5.
- Mean best ground-truth IoU: 0.8565; BD04 was 0.8556.
- Five-breed presence replay: 345/354 accepted detections; BD04 was 344/354.
- Held-out not-target images: 0/54 false-positive images, equal to BD04.

## Remaining failures

`BD05 + M9` errors:

- 24-image set: `Ragdoll_01` -> Sphynx after an accepted detector crop.
- 24-image set: `Pallas_02` -> Sphynx after an accepted detector crop.
- 11-image set: Persian frame `robot-camera-004` -> Ragdoll after detector miss
  and centre fallback.

These small, correlated diagnostic sets are insufficient for a statistically
stable release choice. The next evidence should be a larger unseen robot-camera
session, while keeping both BD04 and BD05 frozen during collection.

## Stage freeze — 2026-07-16

The selected `BD05 + M9` combination is frozen in the repository as:

- `models/frozen/b-d05-manual-curated-screenprint.pt`
- `models/frozen/b-m09-target5-manual-curated-aug.pt`
- `models/frozen/baseline-bd05-m09.toml`
- `models/frozen/baseline-bd05-m09.json`

The JSON record pins both checkpoint hashes, source/augmentation manifest
hashes, routing parameters, and the diagnostic results used for this stage
decision.
