# Baseline Detector-Derived Training Views

Status: **development handoff ready; official Gate B1 remains closed**.

The frozen training path now follows Baseline v1.4:

```text
reviewed base image and frozen parent split
  -> frozen B-D01 (yolo26s.pt, COCO cat detector)
  -> one padded crop when usable, otherwise the original image
  -> exactly one selected view per parent
  -> B-M01 (yolo26s-cls.pt) six-output classifier fine-tuning
```

`B-D01` is not fine-tuned and does not predict breed. It is only an offline
crop generator. `B-M01` remains the only model trained by the supplied training
entry point.

## Frozen dataset

| Class | Detector crop | Original/fallback | Parents |
| --- | ---: | ---: | ---: |
| Ragdoll | 593 | 11 | 604 |
| Singapura | 284 | 14 | 298 |
| Persian | 615 | 59 | 674 |
| Sphynx | 239 | 226 | 465 |
| Pallas | 155 | 145 | 300 |
| not_target | 72 | 374 | 446 |
| **Total** | **1,958** | **829** | **2,787** |

The split remains 85/10/5, every derived view inherits its parent label and
split, and the standard Ultralytics folder tree contains exactly one file per
parent. Detector misses are retained as originals and do not reduce a class.

- Detector SHA-256: `646f8bc3fe0a656803d95c294f7852321748cb29d13466a1af8862e2db384a1b`
- Classifier base-weight SHA-256: `816790029d5df3fef358f03c8144b96339d8824ee25577aeda8be0963e5c5f09`
- View-manifest SHA-256: `c588872eb8a6375895ab5df7e08ba566549ffa5eeab36fe55d8052ddba93ccde`
- Selected-view snapshot SHA-256: `7fdde727679325f45bea03ac3f349c94e2aeadb4e960b719044dce5f3b89f7e9`

## Parallel fine-tuning handoff

Code is frozen in the DeskMate Git repository. After pulling the frozen commit,
extract the one data ZIP at the repository root. Environment bootstrap fetches
the official classifier base weight from the pinned manifest URL and checks its
size and SHA-256. The data ZIP contains only the selected one-view dataset,
manifest, report, and inventory.

| Archive | Size | SHA-256 |
| --- | ---: | --- |
| `deskmate_baseline_data_bd01_views_20260715.zip` | 365,703,437 bytes | `7450d20376974383e642fa23a129ea7a3e05f75ce77f8314da26ccde26da3464` |

After a clean repository extraction, all 2,789 inventoried dataset files passed
size and SHA-256 verification, all 2,787 selected images were present, the
training dry-run passed, and no interrupted-run checkpoint or `runs/` output
was found.

This archive is suitable for parallel development training, not the final
release. Official negative review, provenance/license completion, source
session reconstruction, cross-label dHash adjudication, and multi-box crop
review remain deferred risks.
