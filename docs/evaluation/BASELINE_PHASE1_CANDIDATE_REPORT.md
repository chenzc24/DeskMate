# Baseline Phase 1 Candidate Data Report

> Generated: 2026-07-15 00:57 Asia/Singapore
>
> Status: **CANDIDATE POOL PREPARED — NOT HUMAN ACCEPTED**

## Outcome

The approved Oxford-IIIT Pet, Wikimedia Commons, iNaturalist, and GBIF paths
produced a reproducible Phase 1 candidate pool. After technical filtering and
exact/original-URL deduplication, 1,875 target-cat candidates and 446
`not_target` candidates remain for human review.

This is enough to prepare the release-floor review, but it is not Gate B1:

- all 2,321 reviewable rows remain `pending`/`quarantine`;
- accepted counts are zero;
- the 85/10/5 split is not frozen;
- Selenium is not authorized from candidate counts alone;
- the real robot frame and stream contract remain deferred by the user, so
  Gate B0 also remains `NOT_PASSED`.

## Candidate Coverage

| Label | Unique technical candidates | Gap to 400 | Main review risk |
| --- | ---: | ---: | --- |
| Ragdoll | 450 | 0 | repeated individuals/studio series and adjacent Commons files |
| Singapura | 250 | 150 | strong same-session concentration; second reviewer required |
| Persian | 447 | 0 | illustrations, ambiguous long-hair cats, repeated show series |
| Sphynx | 449 | 0 | repeated cage/show series and same-individual sequences |
| Pallas | 279 | 121 | tiny/absent targets, corpses/tracks, zoo/session repetition |
| `not_target` | 446 | n/a | public negatives still need real robot-background sessions |

The target total is 1,875, which exceeds the 1,200 candidate floor but is 125
below the 2,000 total target. Balanced 400-per-class coverage is short by 150
Singapura and 121 Pallas candidates before human rejection.

## Source Evidence

| Source | Downloaded candidates |
| --- | ---: |
| Commons primary target categories | 250 each for four domestic breeds; 119 Pallas |
| Oxford-IIIT Pet | 200 each Persian/Ragdoll/Sphynx |
| iNaturalist research-grade Pallas | 103 licensed images; source exhausted |
| Commons general Pallas category | 95 noisy candidates; source exhausted |
| GBIF Pallas occurrence media | 100 licensed downloads |
| Commons public negative groups | 6 groups x 75 = 450 |

The official [GBIF occurrence image API](https://techdocs.gbif.org/en/openapi/images)
exposed media license and source metadata, but
96 of its 100 downloads mapped to an already-seen original URL after
normalization. Only four were unique additions. This is why downloaded counts
must never be summed directly across sources. GBIF also warns that media may
carry more restrictive terms than occurrence records, so the pipeline checks
the media-level license rather than trusting the record license alone.

## Technical Audit

- 2,467 raw source rows were combined into a 2,427-row manifest;
- 39 same-ID aliases were collapsed;
- one cross-label Commons ID conflict was rejected;
- seven files failed minimum-dimension or technical checks;
- two exact duplicate clusters were rejected;
- 96 normalized-original-URL duplicate clusters were rejected;
- 18 dHash near-duplicate clusters were flagged for review;
- the manifest auditor reported zero errors and zero warnings;
- assignment example images are absent from the manifest.

Representative contact-sheet inspection showed that dHash under-detects
same-individual and same-session series. In particular, Singapura, Pallas,
Ragdoll, and Sphynx contain visually related sequences that must be grouped by
humans even when their hashes differ.

## Human Review Queue

The ignored local review workspace contains:

- 2,321 stable queue rows;
- 119 contact sheets of at most 20 images;
- zero missing local images;
- preserved first- and second-review decision fields;
- mandatory distinct second reviewers for Singapura, Pallas, and Persian;
- a fail-closed audit that prevents two members of one duplicate cluster from
  both being accepted.

Current review audit: 0 accepted, 0 rejected, 2,321 pending, 0 structural
errors, and `ready_to_freeze_split=false`.

Run the audit after filling the local queue:

```powershell
python scripts/audit_phase1_reviews.py
```

Only accepted/post-dedup counts may authorize targeted Selenium gap-fill or a
frozen 85/10/5 split.

## Next Gate Actions

1. Review all batches, prioritizing Singapura and Pallas, and complete the
   required second review for Singapura/Pallas/Persian.
2. Rerun the review audit and calculate accepted gaps.
3. Use targeted gap-fill only for classes still below 400; guarantee at least
   220 accepted images per target class and at least 1,200 accepted target
   images overall.
4. Accept at least 300 grouped `not_target` images and later add the deferred
   real robot-background sessions.
5. Supply the deferred real robot frame and stream contract before Gate B0/B1
   can be formally frozen.
