# Five-breed detector retraining — 2026-07-16

## Decision

Admit `BD06 + M9` as the default baseline and retain `BD05 + M9` as the
rollback. The canonical runtime config is
`configs/baseline_inference_target5_robot.toml`. On the unchanged 24-image
robot-burst diagnostic, BD06 repaired both
BD05 failures with no regressions: `22/24 -> 24/24`.

This is a development-set result, not a final independent accuracy claim. The
24 images represent eight correlated source bursts.

## Data construction

The source bytes and returned split assignments were preserved. The builder
hard-linked 2,253 original rows into a disposable base view:

| Split/content | Images | Boxes |
|---|---:|---:|
| Five-breed train positives | 1,633 | 1,635 |
| Reviewed train backgrounds | 315 | 0 |
| Five-breed validation positives | 194 | 194 |
| Five-breed test positives | 111 | 111 |

Train-only screen/print augmentation then generated one transformed positive
for every original positive and 462 blank-panel negatives, preserving the BD05
blank-to-positive ratio. Final train size was 4,043 images. Validation and test
images were not augmented.

- Base manifest SHA-256: `c620324343a32cc4e5670d48e00f6bdeb0ae05b22f436731e5e7c3560c369537`
- Augmented manifest SHA-256: `26652f3b63ae72b3666ceed07287cf15dda2c098a4f2cf35e599fb4f42b28bea`
- Synthetic manifest SHA-256: `42209fc8c4c79dca1053191cebb4dd730f07f1d2a5a117ff05c39fca072d6e8a`
- Exact image overlap with the 24-image diagnostic: zero
- Full image/label/hash/box validation: 4,348 rows, 3,575 boxes, zero errors

## Training

- Run: `bd06-fivebreed-screenprint-yolo26s-s20260715-20260716-1351`
- Initialization: official COCO `models/yolo26s.pt`, not BD05
- Requested/completed epochs: 50/35; early stopping patience 10
- Best epoch: 25
- Validation: precision 98.44%, recall 97.73%, mAP50 99.12%, mAP50-95 78.59%
- Frozen checkpoint SHA-256: `edb29b9f78299ad268f0277bbc6bc28bca122283c0943bbf60f23616a61e1cae`

The only training throughput change from BD05 was `workers=4` instead of zero.
Batch, optimizer, learning rates, seed, frozen layers, image size, augmentation,
and early-stopping policy remained unchanged.

## Same-24 full-pipeline comparison

Both runs used frozen M9 and exactly the same route:

```text
detector conf 0.25 -> minimum box area 2% -> 25% padded crop
-> otherwise 80% centre fallback -> M9 classifier
```

| Combination | Correct | Ragdoll | Singapura | Persian | Sphynx | Pallas |
|---|---:|---:|---:|---:|---:|---:|
| BD05 + M9 | 22/24 | 4/5 | 5/5 | 5/5 | 5/5 | 3/4 |
| BD06 + M9 | **24/24** | 5/5 | 5/5 | 5/5 | 5/5 | 4/4 |

Recovered frames:

- `robot-model-test-001` (`Ragdoll_01`): Sphynx 0.5710 -> Ragdoll 0.8002.
- `robot-model-test-022` (`Pallas_02`): Sphynx 0.6356 -> Pallas 0.5145.

Both remained detector-crop routes, so the improvement came from a better ROI,
not from changing the classifier or falling back to the centre. BD06 also
replaced centre fallback with accepted detections on Ragdoll_05, Persian_02,
and Sphynx_03; all three remained correct and classifier confidence increased.

## Detector-only regression

On the common 111-image, five-breed annotated test split:

| Detector | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|
| BD05 | 99.63% | 92.79% | 99.16% | **79.06%** |
| BD06 | 99.01% | **100.00%** | **99.50%** | 78.49% |

BD06 removes the observed misses but trades 0.56 percentage points of stricter
box-tightness mAP. This is the intended trade for the downstream crop-based
classifier. On 54 held-out `not_target` images, both detectors produced zero
accepted false-positive images at the frozen 0.25 confidence and 2% area gate.

## Frozen artifacts

- Candidate: `models/frozen/baseline-bd06-m09.toml`
- Candidate record: `models/frozen/baseline-bd06-m09.json`
- Detector: `models/frozen/b-d06-five-breed-screenprint.pt`
- Rollback: `models/frozen/baseline-bd05-m09.toml`

Both required weights are distributed outside Git history in the
[`bd06-20260716` release](https://github.com/chenzc24/DeskMate/releases/tag/bd06-20260716):

- Detector: `b-d06-five-breed-screenprint.pt`, SHA-256
  `edb29b9f78299ad268f0277bbc6bc28bca122283c0943bbf60f23616a61e1cae`.
- Classifier: `b-m09-target5-manual-curated-aug.pt`, SHA-256
  `d8eb66e7ee102e20efc15b385a4c73781596b38a790356510cb04caaf91cafc1`.

Download both into `models/frozen/` before starting the default runtime.

The next promotion gate remains a larger unseen robot-camera session with both
BD05 and BD06 held fixed.
