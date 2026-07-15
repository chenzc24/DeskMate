# Baseline Human-Screened Cat Intake

Status: **processed, but not ready for split freeze or training**.

The human-screened and teammate-merged images under `data/downloads/cat` were
processed without modifying, renaming, moving, or deleting any originals. The
ignored output under `data/downloads/cat_processed` contains:

- `intake_manifest.csv`: one row for each of the 2,427 source images;
- `clean_candidates/`: 2,341 verified candidate copies in canonical classes;
- `duplicate_review.csv`: seven exact and 32 perceptual duplicate groups;
- `audit.json`: complete generated evidence and checksums.

## Counts

| Label | Raw | Below 160 x 160 | Redundant exact copies | Clean candidate |
| --- | ---: | ---: | ---: | ---: |
| Ragdoll | 604 | 0 | 0 | 604 |
| Singapura | 374 | 69 | 7 | 298 |
| Persian | 675 | 1 | 0 | 674 |
| Sphynx | 474 | 9 | 0 | 465 |
| Pallas | 300 | 0 | 0 | 300 |
| **Total** | **2,427** | **79** | **7** | **2,341** |

All 2,427 images decoded successfully. Every one of the 2,341 materialized
candidate copies matches its source SHA-256. There are no cross-label exact
duplicates, and the source snapshot remained unchanged after processing.

The five target classes meet the 1,200-total/220-per-class release floor, but
do not meet the preferred 400-per-class target: Singapura has 298 and Pallas
has 300 clean candidates.

## Duplicate Review

A dHash Hamming threshold of 4 produced 32 conservative near-duplicate groups
containing 65 images. These rows are grouped for review and split safety; they
were not automatically rejected.

One three-image group crosses labels and needs visual inspection:

- `Persian/Persian_cat_443.jpg`;
- `ragdoll_photos/Ragdoll_cat_196.jpg`;
- `Sphynx - Hairless Cat/Sphynx_cat_451.jpg`.

This may be a visual-hash collision rather than a label problem. The
authoritative review list is the ignored
`data/downloads/cat_processed/duplicate_review.csv`.

## Why Gate B1 Is Still Closed

Human screening establishes that contributors selected the images as the named
breed, but it does not restore provenance removed by sequential renaming and
merging:

- 217 Ragdoll rows retain partial Flickr record/page/download URLs, but no
  recorded author or license;
- 2,210 rows have no recoverable source record in this delivery;
- source-session or same-individual grouping is incomplete;
- this intake has no `not_target` images;
- reviewer identities and decisions are not yet represented in the project's
  strict source/review manifest contract.

Therefore this intake must not replace the existing B1 review queue or be fed
directly into official training yet. The next bounded target should reconcile
provenance/session groups, resolve the 32 near-duplicate groups, merge an
accepted `not_target` set, and only then generate the strict Gate B1 manifest
and 85/10/5 grouped split.

Machine-readable aggregate evidence is in
`BASELINE_HUMAN_SCREENED_INTAKE.json`.
