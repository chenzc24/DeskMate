# Baseline Phase 0 — Gate B0 Audit

> Audit time: 2026-07-14 22:44 Asia/Singapore
>
> Result: **NOT PASSED**
>
> Machine-readable evidence: `BASELINE_PHASE0_B0_REPORT.json`

## Outcome

Phase 0 has a working, deterministic software and data-contract foundation.
The Oxford and `not_target` data-pilot gaps are closed, but Gate B0 is not yet
passed. Two robot-evidence items remain open:

1. one recorded or live frame from the actual robot camera;
2. confirmed robot stream protocol, endpoint/configuration method, orientation,
   and color format.

No Phase 1 accepted-dataset count, model-training result, robot-camera result,
or B0 pass is claimed by this report.

## Deterministic Software Evidence

| Item | Observed value |
| --- | --- |
| OS | Windows 11 `10.0.26200` |
| Python | `3.13.1` |
| GPU | NVIDIA GeForce RTX 4070 Laptop GPU, 8,188 MiB |
| Model | `B-M01-PLACEHOLDER`; no trained weight loaded |
| Robot motion | disabled |

Validation results:

- `python -m compileall -q src tests scripts`: passed;
- `python -m pytest -q tests`: **20 passed**;
- manifest audit: 130 rows, 130 quarantine, 0 errors and 0 warnings;
- assignment example smoke fixture: passed as software-only input;
- confirmation ran before preview, preview emitted no species line, duplicate
  confirmation emitted no second line, stale input cleared temporal state, and
  all queues returned to zero;
- the assignment example remains outside all dataset manifests.

The smoke fixture was `cat-000.png`, 251 x 179 PNG. It is explicitly marked
`assignment_smoke`, `placeholder_only=true`, and `real_robot_evidence=false`.

## Source Pilot Evidence

The bounded pilot used the official
[Wikimedia Action API](https://www.mediawiki.org/wiki/API:Categorymembers),
[iNaturalist API](https://api.inaturalist.org/v1/docs/), and
[Oxford-IIIT Pet](https://www.robots.ox.ac.uk/~vgg/data/pets/) archive.
Wikimedia downloads use 960-pixel thumbnails and remain single-threaded.

| Source / label | Downloaded | Visually usable | Main risk |
| --- | ---: | ---: | --- |
| Wikimedia / Ragdoll | 10 | 3 | coat samples, drawing, silhouette, partial crops |
| Wikimedia / Singapura | 10 | 10 | three images likely share one individual/session |
| Wikimedia / Persian | 10 | 7 | chart, rear-only view, ambiguous breed; one group |
| Wikimedia / Sphynx | 10 | 10 | group/cut-out images need team review |
| Wikimedia / Pallas | 10 | 7 | book page, tiny target, motion blur |
| iNaturalist / Pallas | 10 | 5 | tiny/absent targets and session grouping |
| Oxford / Persian | 10 | 10 | studio/watermark concentration |
| Oxford / Ragdoll | 10 | 10 | first three form a likely shared group |
| Oxford / Sphynx | 10 | 10 | studio/household mix |
| Wikimedia / `not_target` desk | 10 | 10 | historical/diagram-heavy |
| Wikimedia / `not_target` floor | 10 | 7 | three domain-poor items; one shared session |
| Wikimedia / `not_target` mobile robot | 10 | 7 | three circuit diagrams excluded |
| Wikimedia / `not_target` other breed | 10 | 7 | three postage-stamp illustrations excluded |

All 130 images remain `quarantine`. The visual assessment is a single-review
pilot triage with `acceptance_authority=false`; a team reviewer must approve
labels and duplicate/session groups. Accepted counts are therefore zero.

The official Oxford image archive was downloaded once into the ignored data
workspace. It is 791,918,971 bytes with SHA-256
`67195c5e1c01f1ab5f9b6a5d22b8c27a580d896ece458917e61d459337fa318d`.
Only the three bounded 10-image pilot groups were extracted. This is source
evidence, not a frozen training dataset.

The four negative groups provide 40 unique candidates and a documented Phase 1
route to at least 300 grouped negatives: licensed public hard negatives plus
real robot-camera background sessions, with source/session groups kept intact
before the 85/10/5 split. One floor candidate missing a canonical license URL
was rejected before the final manifest.

Selenium was not installed or used. There is still no human-accepted,
post-dedup coverage report that could authorize gap-fill scraping.

## Gate B0 Checklist

| Check | Result | Evidence |
| --- | --- | --- |
| Six internal / five reportable labels | PASS | exact order tested and config-checked |
| Manifest provenance and quarantine separation | PASS | 130 rows, 0 errors/warnings |
| Configured source/class pilots | PASS | 13/13 groups reached 10 images |
| Pilot visual risk triage | PASS | 13 contact sheets and review summary |
| Oxford source image pilot | PASS | three labels x 10; archive SHA-256 recorded |
| `not_target` source pilot | PASS | four groups, 40 candidates, Phase 1 route |
| Compile and deterministic tests | PASS | 20 tests passed |
| Bounded runtime / console behavior | PASS | smoke report and tests |
| Actual robot-camera frame | **FAIL** | no recorded/live robot media available |
| Robot stream contract | **FAIL** | protocol/endpoint/orientation/color unknown |
| Selenium held behind gap report | PASS | `selenium_used=false` |
| Calibration remains unfrozen | PASS | temperature/threshold flags false |

## Evidence Checksums

Authoritative checksum values are stored in
`BASELINE_PHASE0_B0_REPORT.json`. They cover Phase 0/source/review configs, the
ignored pilot manifest/report, and the ignored skeleton smoke report.

## Required Actions To Pass B0

1. Obtain the robot stream protocol, endpoint/configuration method, stable
   resolution and FPS, BGR/RGB/YUV format, rotation, reconnect behavior, and
   responsible Robotics owner.
2. Save one consented recorded/live robot frame and rerun the skeleton with
   `--source-kind recorded_robot` or `live_robot`; verify dimensions,
   orientation, color treatment, timestamp, and stale-frame behavior.
3. Regenerate `BASELINE_PHASE0_B0_REPORT.json`. B0 passes only when every
   machine-readable check is true.
