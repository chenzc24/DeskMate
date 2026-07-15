# Baseline Phase 0: Foundation, Data Sources, And Runtime Skeleton

## Goal

Synchronize the first executable Baseline phase with the hardened v1.2
architecture so the team can start immediately without confusing source audit,
bulk acquisition, model training, or final evaluation. Phase 0 must establish
the robot-video/runtime skeleton, five reportable labels plus internal
`not_target`, data-source priority, reproducible manifests, bounded worker
contracts, and objective entry conditions for Phase 1.

## Dirty-State Note

The worktree already contains the uncommitted Baseline/Advanced split, plan
organization, YOLO-classification revision, dataset-first Phase 0 revision, and
subsequent architecture hardening. The hardened Baseline v1.2 decisions are
inputs to this synchronization, not changes to be undone. No existing dirty
path will be discarded or staged.

## Owned Files

- `plan/2026-07-14-baseline-phase-0-foundation/plan.md` — synchronized Phase 0
  execution target.
- `plan/log.md` — factual documentation-validation outcome.

## Read-Only Files And External State

- `References/The requirement/**` — authoritative assignment evidence.
- `docs/plans/BASELINE_PLAN.md` — hardened v1.2 governing principle for this
  target; this synchronization does not change it.
- `docs/plans/ADVANCED_PLAN.md` and Advanced dataset documents.
- `AGENTS.md` and `README.md`.
- `plan/2026-07-14-harden-baseline-architecture/**` and all prior target plans.
- `scripts/download_dataset_sources.ps1` — belongs to Advanced desk-object data.
- The user's browser/driver preparation for the referenced Selenium tutorial;
  this target does not install packages or run a scraper.
- All source code and data directories until a later implementation target
  explicitly owns them.

## Dependencies And Evidence To Review

- The assignment's five breeds, 85/15 target split, approximate 1,000-image
  guidance, transfer-learning choice, and live robot-camera requirement.
- The referenced Selenium/Google-image tutorial and its operational risks.
- Official or maintainer-hosted datasets/APIs that cover the five classes,
  including class counts, licenses, provenance, and download stability.
- Hardened Baseline contracts: five reportable labels plus internal
  `not_target`, `val_select`/`val_cal`, separate `robot_calibration`/
  `robot_final`, `ModelRunner[OutputT]`, `ClassificationObservation`, quality
  gates, and bounded capture/preview/confirmation queues.
- Local RTX 4070; robot stream details are still required from the Robotics
  team but no motion is needed for this documentation target.

## Decision Questions

1. Which classes have trustworthy existing labeled data?
2. Which classes require targeted API download or scraping?
3. What counts as a unique base image for the 1,200/2,000/3,000 gates?
4. When is Selenium allowed to enter the critical path?
5. Which negative scenes establish the `not_target` contract without polluting
   the five-breed report counts?
6. Which minimal queue, freshness, and output-contract fixtures prove the live
   skeleton is safe to extend before model training?
7. What exact artifacts prove Phase 0 is complete before bulk download/training?

## Frozen Decision

- Use a hybrid, dataset-first acquisition policy; do not put unrestricted web
  scraping on the Baseline critical path.
- Use Oxford-IIIT Pet as the primary source for Persian, Ragdoll, and Sphynx;
  use Wikimedia Commons API as a traceable supplement.
- Use licensed, research-grade iNaturalist observations plus Wikimedia Commons
  for Pallas; use Wikimedia Commons and audited secondary sources for
  Singapura.
- Treat Hugging Face/Kaggle collections as candidates, not trusted authorities,
  until their cards prove label definitions, original provenance, license, and
  duplicate status.
- Run Selenium only after accepted, licensed, post-dedup coverage is measured.
  Gap-fill a class below 400 with a 25% review buffer, and never write scraped
  candidates directly into a frozen split.
- Collect 300–600 `not_target` images separately from the five target counts;
  group real backgrounds and video-derived samples by source/session, and do
  not allow adjacent frames to cross splits.
- Freeze six internal outputs in the manifest while keeping only the five cat
  breeds reportable. Exact internal order is `ragdoll / singapura / persian /
  sphynx / pallas / not_target`; `not_target` never produces a species census
  record.
- Keep the user's browser preparation. After package installation in a later
  implementation target, first test Selenium Manager through the minimal
  `webdriver.Chrome()` path; use a manually pinned driver only if that fails.
- Build the Phase 0 runtime skeleton around `FramePacket`, bounded latest-frame
  capture, and `ModelRunner[OutputT]`. The Baseline task output is
  `ClassificationObservation`; it must not expose Torch or Ultralytics objects
  to UI, logging, or scheduling code.
- Preview output may update UI state but must not print a species line. Only a
  fresh, quality-gated confirmation event may print and register a species.

## Phase Boundary

Phase 0 freezes six internal labels, source/manifest contracts, small target and
negative-source pilots, robot stream facts, and the bounded
robot-frame-to-placeholder-observation/UI skeleton. Phase 1 owns bulk target and
`not_target` acquisition, review, deduplication, the objective Selenium
go/no-go, and the grouped 85/10/5 split freeze. Phase 2 owns the first
`yolo26s-cls` training run and real-stream integration; additional seeds or
challengers remain evidence-gated. Phase 3 owns temperature/threshold fitting,
robot-domain calibration, one untouched final evaluation, reliability, and
release freeze. Phase 4 owns official evaluation and report submission.

## Expected Phase 0 Output

- Five reportable labels, internal `not_target`, display names, and exact output
  order frozen.
- Source matrix with primary, secondary, and gap-fill source per class.
- Dataset manifest schema, target/negative count separation, source/session
  groups, duplicate clusters, and split policy frozen.
- Target-source pilots cover each configured source/class pair; negative pilots
  cover real robot background, other cats, blur/exposure failures, and partial
  posters without counting adjacent frames as unique images.
- Robot/video protocol, resolution, FPS, color/rotation, reconnect, recording,
  display, and emergency-owner facts recorded with the Robotics team.
- `FramePacket -> ModelRunner[ClassificationObservation] -> aggregator -> UI /
  confirmation console` skeleton specified for implementation, with no
  framework-native result crossing the runner boundary.
- Capture uses a bounded latest-frame buffer; preview has at most one pending
  job; confirmation cannot block capture, remote control, or the UI event loop.
- Deterministic fixtures cover stale/missing frame invalidation, queue drop,
  blur/exposure/age/ROI-quality reasons, `not_target`, preview-without-console,
  and confirmation console format. Phase 0 verifies the metric/reason plumbing;
  Phase 3 freezes calibrated thresholds.
- A download/scrape go/no-go rule based on post-dedup per-class coverage.
- Phase 0 exit gate and Phase 1 entry checklist with named evidence.

## Gate B0 Evidence Checklist

- [ ] Six internal labels and five reportable display names match the governing
  Baseline plan.
- [ ] Manifest template contains provenance/license, source/session group,
  exact/perceptual hash, review, duplicate-cluster, and split fields.
- [ ] Every configured target source/class pair has a 10–20 image pilot with
  success, label-error, license-missing, and duplicate-risk counts.
- [ ] Representative `not_target` source pilots and the Phase 1 route to at
  least 300 grouped negatives are documented.
- [ ] At least one recorded or live robot frame reaches the UI skeleton with a
  valid `FramePacket` timestamp and the correct orientation/color treatment.
- [ ] A placeholder `ClassificationObservation` reaches UI/aggregator through
  the generic runner boundary; UI/logging code does not read framework-native
  model objects.
- [ ] Preview produces no species console line; a deterministic confirmation
  fixture produces the specified confirmed-species line exactly once.
- [ ] Stale/missing frames clear temporal state; full preview queues drop old
  jobs; confirmation does not block capture/UI in the deterministic harness.
- [ ] Robotics stream/reconnect/display facts, owners, and Phase 1 data/review
  owners are named.
- [ ] Selenium remains disabled until the Phase 1 post-dedup coverage report
  demonstrates a target-class gap below 400.

## Validation

- Cross-check all hard decisions against the four requirement transcriptions.
- Cite direct dataset/API sources and distinguish verified facts from proposed
  counts that must be measured after download.
- Ensure the strategy cannot mix near-duplicates across the 85/15 split or use
  the five assignment examples for training.
- Ensure `not_target` is excluded from the five-cat report count, grouped by
  source/session, and never printed as a species.
- Ensure the target plan does not move calibration or `robot_final` evidence
  into Phase 0 and does not require a challenger before the first live model.
- Ensure interface names and console behavior match the hardened Baseline and
  obsolete backend-boundary/preview-console assumptions are absent.
- Check local Markdown links, code fences, whitespace, `git diff --check`, and
  final status scope.

## Recorded-Video And Robot Validation

No physical motion. Phase 0 implementation later must prove that at least one
recorded or live robot frame reaches the bounded UI/observation skeleton and
exercise stale-frame behavior; this documentation revision does not claim those
runtime results.

## Commit Intent

Do not commit or push automatically. Leave the bounded plan revision for human
review.

## Validation Results

- Confirmed `References/The requirement/**` remains unchanged.
- Confirmed the synchronized target includes the exact six-output order,
  separate 300–600 `not_target` policy, `ModelRunner[OutputT]`,
  `ClassificationObservation`, bounded preview/confirmation behavior,
  85/10/5 Phase 1 freeze, Selenium go/no-go, and calibration/final separation.
- Confirmed obsolete five-output, placeholder-backend, and legacy interface
  wording is absent.
- Confirmed Gate B0 does not fit temperature, run `robot_final`, or train a
  challenger; those actions remain in later phases.
- Confirmed owned Markdown has balanced code fences and no trailing whitespace;
  `git diff --check` passed.
- Final status review found the existing uncommitted plan moves/revisions plus
  this synchronized target. Nothing was staged, committed, pushed, installed,
  downloaded, or executed against a robot.
