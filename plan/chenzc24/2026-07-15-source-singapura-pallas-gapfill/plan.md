# Source Singapura And Pallas Gap-Fill Candidates

## Goal

Create two independent human-review folders containing new Singapura and
Pallas candidates. Target roughly 180--220 candidates per class so that the
team can retain about 100 unique images and bring both classes near 400.

## Owned files

- `scripts/source_singapura_pallas_gapfill.py`
- generated ignored `data/downloads/baseline_additional_review_20260715/`
- this plan

## Read-only inputs

- `data/downloads/baseline_provisional_split/provisional_split_manifest.csv`
- `data/downloads/phase1_candidates/`
- all frozen handoff datasets and checkpoints
- unrelated concurrent dirty files

## Sources and dependencies

- Wikimedia Commons `Category:Singapura`, including its breed-specific
  subcategories, with source page, author, and license metadata.
- iNaturalist research-grade `Otocolobus manul` observations and GBIF licensed
  still images for Pallas.
- Existing unused Phase-1 Pallas candidates may be reused only when their exact
  hash is absent from the frozen split.

## Validation

- Exclude every exact SHA-256 already present in the frozen split.
- Reject files below 160x160, exact duplicates within the new pool, and images
  without source/license metadata.
- Decode every materialized image and write one manifest per review folder.
- Record counts by source and reasons for exclusions.

## Robot motion

No robot connection or motion is involved.

## Commit intent

No commit or push. Downloaded images remain ignored; only the reproducible
acquisition script and plan may be committed later if requested.

## Result

- Singapura review folder: 204 unique Wikimedia Commons candidates.
- Pallas review folder: 220 unique candidates (100 GBIF, 102 iNaturalist, 18
  Wikimedia Commons).
- All 424 files decoded successfully, have complete source/license fields, are
  exact-hash unique within their folder, and have zero exact-hash overlap with
  the 2,787-image frozen split.
- Status remains `PENDING_HUMAN_REVIEW`; nothing was merged into a training
  split or used for training.
