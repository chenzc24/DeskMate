# Baseline Pretrained Cat Localizer Smoke

Status: **smoke complete; not release admitted; disabled by default**.

The official COCO-pretrained Ultralytics `yolo26s.pt` detection weight loaded
on the local RTX 4070. Its native class names resolved exactly one `cat` entry
at class ID 15. The adapter emitted only typed normalized boxes; no breed,
classification probability, census event, console species line, or motor
command can originate from `B-D01`.

## Asset Identity

| Item | Value |
| --- | --- |
| Model | `B-D01` / YOLO26s Detect |
| Source release | Ultralytics assets `v8.4.0` |
| Weight | ignored `models/yolo26s.pt` |
| Bytes | 20,422,725 |
| SHA-256 | `646f8bc3fe0a656803d95c294f7852321748cb29d13466a1af8862e2db384a1b` |
| Runtime | Ultralytics 8.4.95 / PyTorch 2.11.0+cu128 |
| Hardware | NVIDIA GeForce RTX 4070 Laptop GPU |
| Initial input size | 640 |

## Assignment-Example Smoke

All five assignment example images produced one cat proposal at the provisional
0.25 confidence threshold. Top proposal confidence ranged from 0.7341 to
0.9530. After one per-image warm-up, 25 measured predictions produced a
37.71 ms mean and 44.52 ms P95. These numbers cover detector inference on five
local files only; they exclude capture, temporal stability, crop routing,
classification, UI, and network transport and are not a release claim.

The assignment examples remain smoke-only inputs and are excluded from all
training data. Five successful examples do not measure false proposals,
printed-card recall, temporal stability, or robot-camera domain performance.

## Safe Structure

- `LocalizerObservation` contains normalized boxes, confidence, model/frame
  identity, timestamps, validity, and reason; it contains no breed field.
- Native Ultralytics results and tensors remain inside the adapter.
- Only a same-frame box separately declared temporally stable may route a
  padded crop.
- Missing, stale, malformed, wrong-frame, unstable, or empty output routes to
  the centre ROI.
- The active classifier contract and all B0/B1 outcomes are unchanged.

## Remaining Admission Work

After the real robot video arrives and the centre-ROI classifier path works,
compare on the same frozen clips:

1. centre ROI plus `B-M01`;
2. detector crop plus `B-M01`;
3. detector crop with centre-ROI fallback plus `B-M01`.

Record stable-box success, false proposals, stale/missing rate,
time-to-first-stable-box, end-to-end time-to-confirm, FPS, and P95 latency.
Keep `B-D01` disabled unless the fallback configuration improves confirmation
time without reducing the frozen target/rejection gates.
