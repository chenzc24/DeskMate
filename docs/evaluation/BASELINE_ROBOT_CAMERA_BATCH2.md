# Robot-Camera Batch 2: Detector To Classifier

The current filesystem snapshot contains nine 640×480 PNG frames: the previous
three Sphynx images and six new images. The two files briefly visible as
`1253/1254` during upload were no longer present when the frozen evaluation
snapshot was read, so they are not counted.

All nine images were rerun through the unchanged active pipeline. The table
below covers only the six new images. Labels come from visible text printed on
the paper and human inspection; they are useful descriptive evidence, not a
formal frozen ground-truth set.

| Frame | Visible label | Route | Prediction | Confidence | Descriptive result |
| --- | --- | --- | --- | ---: | --- |
| 4 | Persian | centre fallback | Persian | 90.23% | correct |
| 5 | Ragdoll | detector crop | Ragdoll | 99.21% | correct |
| 6 | Persian | detector crop | Persian | 99.997% | correct |
| 7 | Singapura | detector crop | Singapura | 77.42% | correct |
| 8 | Pallas | detector crop | Persian | 80.28% | wrong |
| 9 | Pallas | centre fallback | Persian | 48.56% | wrong |

Descriptively, the active chain got 4/6 new images. Detector routing succeeded
on 4/6. All non-Pallas images were correct; both Pallas images failed.

## Failure diagnosis

Frame 8 proves that the Pallas issue is not only detector recall: `B-D01`
accepted a cat box at confidence 0.260 and the routed crop still produced
Persian at 80.28%. Full, 0.8-centre, and 0.6-centre views also failed to make
Pallas top-1.

Frame 9 received native cat proposals with only 0.0167 and 0.0137 confidence,
well below the active 0.25 threshold. Lowering only the area floor to 1% does
not recover it. Its full/medium/tight centre views likewise returned
`not_target` or Persian rather than Pallas.

Frame 4 is a useful counterexample: its detector confidence was only 0.0477,
but the centre fallback correctly predicted Persian at 90.23%. Detector misses
therefore do not automatically imply mission failure when the target is framed
well enough for fallback.

The six new images averaged 40.20 ms for detector plus classifier model calls.
This small still batch does not support FPS or P95 claims.

## Decision

Do not lower detector confidence merely to fix these Pallas frames: 0.0167 is
too low to admit without measuring false proposals on backgrounds. The stronger
next action is a Pallas print-domain calibration set, kept separate from the
final test, plus additional empty/background frames. Compare detector crop and
centre ROI on that same set before retraining or changing thresholds.

All annotated frames, routed crops, contact sheet, per-frame CSV, full top-3
probabilities, low-confidence proposals, and multi-scale diagnostics are under
`artifacts/robot_camera_eval/batch_20260715_1237/`.
