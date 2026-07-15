# Robot-Camera Still Test: Detector To Classifier

Three 640×480 PNG frames from `data/downloads/Camera/` were passed through the
current chain:

```text
B-D01 COCO cat detector
  -> 15% padded detector crop or 0.8 centre fallback
  -> B-M01 detector-view classifier best.pt
```

The paper in all three frames visibly says Sphynx and visually contains a
Sphynx image. This is a useful expectation for diagnosis, but it is not a
frozen ground-truth manifest and therefore does not support a formal accuracy
claim.

## Active configuration result

| Frame | Detector | Route | Classifier | Confidence | Margin |
| --- | --- | --- | --- | ---: | ---: |
| Near | cat 0.709, area 9.09% | detector crop | Sphynx | 99.999% | 99.999% |
| Medium | cat 0.865, area 6.27% | detector crop | Sphynx | 99.9998% | 99.9997% |
| Far | no accepted box | centre fallback | not_target | 49.79% | 16.43% |

Two of three frames completed the intended detector-crop-classifier route and
produced Sphynx. The far frame failed the active route.

The far-frame failure is specifically caused by the current minimum-area gate,
not by the absence of a detector proposal. Native `B-D01` produced a cat box
with confidence 0.376 and area 1.26%; the active minimum is 2.00%, so the typed
localizer correctly filtered it out.

A diagnostic-only rerun with minimum area 1.00% accepted that same proposal.
The resulting padded crop was classified as Sphynx with 99.13% confidence and
98.63% margin. This is strong evidence to sweep the area threshold on more
robot frames, but three images are insufficient to change the release config.

## Latency

| Component | Three-frame mean |
| --- | ---: |
| Detector | 97.84 ms |
| Classifier | 15.18 ms |
| Model chain | 113.03 ms |

The first detector frame took 194.09 ms despite model warmup; the next two took
35.41 and 64.03 ms. Three stills are insufficient for an FPS or P95 claim.

Annotated images, routed crops, the contact sheet, full box coordinates, top-3
probabilities, and CSV/JSON output are under `artifacts/robot_camera_eval/`.

Recommended next test: collect at least 20–30 frames across distance and angle,
then compare minimum-area values 0.005/0.01/0.015/0.02 on exactly the same
frames. Keep confidence at 0.25 during that comparison and measure false cat
boxes on empty/background frames before changing the active threshold.
