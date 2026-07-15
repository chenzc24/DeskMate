# Baseline Provisional Development Split

Status: **ready for provisional development training; official Gate B1 remains
closed**.

Following the user's risk decision, the processed human-screened target intake
was combined with all 446 technically valid original Phase 1 `not_target`
candidates. Author/license completion and manual dHash adjudication are deferred
for this development artifact.

The ignored output is under
`data/downloads/baseline_provisional_split/`:

- `provisional_split_manifest.csv`: 2,787 grouped split rows;
- `provisional_split_report.json`: complete generated evidence;
- `yolo_classify/`: six-class `train`, `val`, and `val_cal` directories.

## Split Counts

| Label | Train | Val-select | Val-cal | Total |
| --- | ---: | ---: | ---: | ---: |
| Ragdoll | 513 | 61 | 30 | 604 |
| Singapura | 253 | 30 | 15 | 298 |
| Persian | 573 | 67 | 34 | 674 |
| Sphynx | 395 | 47 | 23 | 465 |
| Pallas | 255 | 30 | 15 | 300 |
| `not_target` | 379 | 45 | 22 | 446 |
| **Total** | **2,368** | **280** | **139** | **2,787** |

The allocation exactly matches the requested 85/10/5 rounded per-class counts.
All 2,787 materialized copies passed SHA-256 verification. Known source groups,
same-label dHash groups, and exact hashes have zero cross-split leakage.

Cross-label dHash-only collisions were ignored as requested because they are not
exact-content matches. Cross-label exact content remains a hard failure; none
was found.

## Deferred Risks

- Target author and license completion is postponed.
- Source-session reconstruction is incomplete for renamed/merged target files.
- The original `not_target` rows are technically filtered but still show
  pending decisions in the official review queue.
- dHash clusters were grouped for leakage safety without manual adjudication.

These risks do not block a first development training run, but this split must
not be presented as the final Gate B1 release split or used for untouched final
metrics. The official B1 review/gate files were not modified.

Machine-readable evidence is in `BASELINE_PROVISIONAL_SPLIT.json`.
