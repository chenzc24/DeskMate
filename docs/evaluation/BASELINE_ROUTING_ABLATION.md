# Baseline ROI Routing Ablation

Status: **routing hardening supported for development; not release-admitted**.

## Decision

Adopt this development configuration:

- keep detector confidence at `0.25`;
- lower the detector area floor from `0.02` to `0.01`;
- reject a padded detector crop whose source-pixel short side is below `64`;
- remove near-duplicate proposals at IoU `0.85` before downstream candidate use;
- retain the centred `0.8` ROI whenever no acceptable proposal remains.

A normalized crop-size threshold was rejected because it would discard valid
small subjects in the actual 640x480 robot view.

## Same-Image Result

| Diagnostic set | Control | Hardened | Corrections | Regressions |
| --- | ---: | ---: | ---: | ---: |
| Deliberately biased original 40 | 37/40 | 38/40 | 1 | 0 |
| Expanded mixed-split 600 | 588/600 | 588/600 | 0 | 0 |
| Robot-camera stills with visible labels | 6/9 | 7/9 | 1 | 0 |

The 64-pixel gate rejected the 31-pixel false crop in
`target-sphynx-000158`; centre fallback then changed `not_target` to the correct
`sphynx`. The 1% area floor admitted the far robot Sphynx proposal with 1.26%
area and changed `not_target` to `sphynx`. The frozen control predictions were
reproduced exactly on all 640 non-robot diagnostic images.

IoU de-duplication removed a near-duplicate in 12 samples, including the known
multi-box Singapura cases. It did not change the selected route or prediction;
its benefit is preventing redundant downstream candidate work, not repairing
breed errors.

A robot-only detector sweep also classified every extra proposal between
confidence 0.01 and 0.25. All four were wrong: the two low-confidence Pallas
proposals were still classified Persian, while extra Sphynx/Persian proposals
became `not_target`/Ragdoll. Lowering the global detector confidence therefore
adds false candidates and does not recover Pallas, so confidence remains 0.25.

## What Remains Unsolved

Routing hardening does not repair the robot-print Pallas domain gap. Pallas was
99/100 in the expanded in-domain diagnostic but 0/2 on robot stills, with both
robot images predicted as Persian. Singapura was 96/100 in the expanded set and
1/1 on the robot stills. Therefore neither a lower detector threshold nor
top-K box classification is justified as the next classifier fix.

The next model target needs independent robot-view Singapura and especially
Pallas base images, split by capture session before fine-tuning. These nine
diagnostic images must not be reused as claimed final-test evidence if any are
used for development.

## Runtime And Scope

On the RTX 4070 Laptop GPU with Torch 2.11.0+cu128 and Ultralytics 8.4.95, the
warmed static component diagnostic measured detector 32.98 ms mean / 38.34 ms
P95 and classifier 15.19 ms mean / 21.75 ms P95. Identical ROI classifications
were cached across policies, so this is not an end-to-end camera benchmark.

The 40-image set is deliberately biased, the 600-image set contains training
and validation parents, the robot labels are read from the visible printed
pages rather than a frozen manifest, and probabilities are uncalibrated. None
of these numbers is release accuracy.

Generated evidence is under
`data/downloads/baseline_routing_ablation/`; the reproducible runner is
`scripts/evaluation/compare_baseline_routing.py`.
