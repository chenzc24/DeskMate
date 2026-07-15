# Baseline Provisional Detector-View Classifier Training

Status: **training complete; development checkpoint only**.

The frozen COCO `B-D01` detector had already produced one selected padded crop
or original fallback for each parent. This run trained only the six-output
`B-M01=yolo26s-cls.pt` classifier on those fixed views.

## Run result

| Item | Result |
| --- | ---: |
| Configured epochs | 50 |
| Completed epochs | 19, early stopped with patience 12 |
| Best epoch in `results.csv` | 7 |
| Best train loss | 0.15007 |
| Best validation loss | 0.17156 |
| Best validation top-1 | 95.71% |
| Best validation top-5 | 100.00% |
| Independent validation macro F1 | 95.81% |
| Wall time | 139.55 seconds |

The final epoch reached train loss 0.05384 but validation loss rose to 0.40026
and top-1 fell to 92.86%. Early stopping therefore correctly retained the epoch
7 `best.pt` rather than `last.pt`.

## Per-class validation

| Class | Support | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| Ragdoll | 61 | 98.31% | 95.08% | 96.67% |
| Singapura | 30 | 96.67% | 96.67% | 96.67% |
| Persian | 67 | 92.96% | 98.51% | 95.65% |
| Sphynx | 47 | 97.87% | 97.87% | 97.87% |
| Pallas | 30 | 96.77% | 100.00% | 98.36% |
| not_target | 45 | 92.86% | 86.67% | 89.66% |

The weakest result is `not_target` recall. Six of 45 negative validation images
were predicted as a target class, so rejection and robot-background testing are
still required before release.

Selected crop views scored 183/193 (94.82%); original/fallback views scored
85/87 (97.70%). This difference is diagnostic, not a controlled causal
comparison, because the two subsets contain different images and class mixes.

## Frozen checkpoint

- Path: `runs/baseline_provisional/b-m01-provisional-bd01-oneview-seed-20260715/weights/best.pt`
- Size: 11,035,778 bytes
- SHA-256: `c41cfd4a12411883df52bf8643b20a2621b189bbd27c642bae441e92cf06319d`
- Native order: `0_ragdoll / 1_singapura / 2_persian / 3_sphynx / 4_pallas / 5_not_target`

The checkpoint was independently loaded on the RTX 4070 and reproduced
268/280 correct predictions, 95.71% top-1, and 95.81% macro F1 on `val_select`.
`val_select` selected the epoch and is not final-test evidence. `val_cal`, robot
calibration, and robot-final data remain untouched.
