# Merged Gap-Fill Classifier Training

Status: **training complete; development candidate, not promoted**.

## Training

- Dataset: `data/downloads/baseline_merged_gapfill_20260715/one_view_yolo_classify`
- Model initialization: `yolo26s-cls.pt`
- Seed: `20260715`
- Completed epochs: 13 (early stopping)
- Best epoch: 1 (zero-based)
- Best training validation top-1/top-5: 95.19% / 100%
- Runtime: 160.79 seconds on the RTX 4070 Laptop GPU
- Best checkpoint SHA-256: `800e36488de1afa9e7d0906b0ba4e864301f704942887482737b7928ee984ae0`

## Same-dataset comparison

| Evaluation subset | Frozen model | Merged gap-fill model |
| --- | ---: | ---: |
| Full `val` (291) | 96.56% | 95.19% |
| Existing-only `val` (272) | 97.06% | 94.85% |
| New gap-fill `val` (19) | 89.47% | 100.00% |
| `val_cal` (145) | 96.55% | 96.55% |

The candidate learned all 19 new Singapura/Pallas validation views but lost
six additional correct predictions on the existing validation subset. On
`val_cal`, Singapura improved from 19/20 to 20/20, while `not_target` fell from
18/19 to 17/19.

## Robot-camera stills

Both classifiers scored 6/9 using the same saved routed crops and human-read
printed labels. The new candidate corrected both Pallas stills, but regressed
one Persian still to `not_target` and the Singapura still to Sphynx. This is
descriptive evidence, not held-out release accuracy.

## Decision

Do not replace the frozen classifier with this checkpoint. It is useful as an
ablation showing that the new source data teaches Pallas, but the current
training recipe trades away existing-domain and Singapura robustness. A next
candidate should preserve the frozen model through lower-rate continuation,
replay-balanced sampling, or checkpoint fusion and must beat it on the same
existing, new-source, rejection, and robot subsets.
