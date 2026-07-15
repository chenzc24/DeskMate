# Baseline Phase 0: Foundation, Data Sources, And Runtime Skeleton

## Goal

Synchronize the first executable Baseline phase with the v1.3
architecture so the team can start immediately without confusing source audit,
bulk acquisition, model training, or final evaluation. Phase 0 must establish
the robot-video/runtime skeleton, five reportable labels plus internal
`not_target`, data-source priority, reproducible manifests, bounded worker
contracts, and objective entry conditions for Phase 1.

The 2026-07-15 refresh also records the annotation-free assisted-localization
decision without changing Gate B0: an official COCO-pretrained detector may
propose cat-content boxes for the classifier, while centre ROIs remain the
mandatory fallback and the release works with the detector disabled.

## Dirty-State Note

The worktree contains active 2026-07-15 robot-JPEG-default and review-handoff
changes in configuration, evaluation reports, scripts, tests, and other target
plans. They are external evidence and remain read-only here. The Baseline v1.3
principles are inputs to this Phase 0 refresh; no existing dirty path will be
discarded or staged.

## Owned Files

- `plan/2026-07-14-baseline-phase-0-foundation/plan.md` — synchronized Phase 0
  execution target.
- `plan/log.md` — factual documentation-validation outcome.

## Read-Only Files And External State

- `References/The requirement/**` — authoritative assignment evidence.
- `docs/plans/BASELINE_PLAN.md` — v1.3 governing principle, updated by the
  separate `2026-07-15-add-pretrained-cat-localizer` target.
- `docs/plans/ADVANCED_PLAN.md` and Advanced dataset documents.
- `AGENTS.md` and `README.md`.
- `plan/2026-07-14-harden-baseline-architecture/**` and all prior target plans.
- `scripts/data/download_dataset_sources.ps1` — belongs to Advanced desk-object data.
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
- Official COCO-pretrained `yolo26s.pt` for optional `cat` localization;
  `yolo26n.pt` is a latency fallback. Neither requires project detector labels.
- Local RTX 4070. Robot video is being handed over, but the real frame and
  delivery contract are still required from the Robotics team; no motion is
  needed for this documentation target.

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
- Treat `B-D01=yolo26s.pt` as an optional, pretrained COCO `cat` proposal
  source. It never predicts breed, never prints a species, never sends motor
  commands, and never changes B0/B1. Stable boxes are padded and classified by
  `B-M01`; missing/stale/invalid boxes immediately select centre ROIs.
- Do not annotate or fine-tune a Baseline detector. If the pretrained localizer
  does not improve time-to-confirm on the same robot videos without metric
  regression, disable it. Record source/version/hash/license/class mapping if
  it is admitted.
- After human acceptance, deduplication, and grouped 85/10/5 split freeze, use
  the same pinned `B-D01` offline to derive padded classifier views. Every crop
  inherits `parent_image_id` and split, never increases official counts, and
  never causes a detector-miss parent to be removed.
- Train `B-M01` with base-image-balanced original/crop view selection rather
  than flattening both files into a folder loader. Other-breed cat crops remain
  `not_target`; no-cat backgrounds retain original/centre views; robot and
  assignment media remain excluded.
- If the multi-view loader is not deterministically verified before first
  training, materialize exactly one view per parent (valid crop, otherwise
  original). This preserves the existing folder trainer and prevents the data
  enhancement from blocking the first seed or double-weighting detector hits.

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

The annotation-free `B-D01` decision is documented in Phase 0. A separate
bounded smoke target has since exercised the official weight and typed crop
router, but neither that smoke nor derived training views change B0/B1. Offline
crop derivation begins only after B1 freezes accepted base-image splits; online
same-video admission remains Phase 2 after the `B-M01` centre-ROI live path.

## Expected Phase 0 Output

- Five reportable labels, internal `not_target`, display names, and exact output
  order frozen.
- Source matrix with primary, secondary, and gap-fill source per class.
- Dataset manifest schema, target/negative count separation, source/session
  groups, duplicate clusters, and split policy frozen.
- Derived-view policy freezes split-before-derive, parent/split inheritance,
  detector-miss retention, base-balanced sampling, official count exclusion,
  and assignment/robot-test exclusion; implementation is not a B0 artifact.
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
- The optional localizer now has a bounded smoke-tested `LocalizerObservation`
  adapter and same-frame padded crop router with contract tests; release queue
  integration and robot-video admission remain later work. Missing/stale/
  multi-box cases must keep centre fallback immediate and console output
  classifier-only.
- Deterministic fixtures cover stale/missing frame invalidation, queue drop,
  blur/exposure/age/ROI-quality reasons, `not_target`, preview-without-console,
  and confirmation console format. Phase 0 verifies the metric/reason plumbing;
  Phase 3 freezes calibrated thresholds.
- A download/scrape go/no-go rule based on post-dedup per-class coverage.
- Phase 0 exit gate and Phase 1 entry checklist with named evidence.

## Gate B0 Evidence Checklist

- [x] Six internal labels and five reportable display names match the governing
  Baseline plan.
- [x] Manifest template contains provenance/license, source/session group,
  exact/perceptual hash, review, duplicate-cluster, and split fields.
- [x] Every configured target source/class pair has a 10–20 image pilot with
  success, label-error, license-missing, and duplicate-risk counts.
- [x] Representative `not_target` source pilots and the Phase 1 route to at
  least 300 grouped negatives are documented.
- [ ] At least one recorded or live robot frame reaches the UI skeleton with a
  valid `FramePacket` timestamp and the correct orientation/color treatment;
  robot video is currently in handoff and is not yet accepted evidence.
- [x] A placeholder `ClassificationObservation` reaches UI/aggregator through
  the generic runner boundary; UI/logging code does not read framework-native
  model objects.
- [x] Preview produces no species console line; a deterministic confirmation
  fixture produces the specified confirmed-species line exactly once.
- [x] Stale/missing frames clear temporal state; full preview queues drop old
  jobs; confirmation does not block capture/UI in the deterministic harness.
- [ ] Robotics stream/reconnect/display facts, owners, and Phase 1 data/review
  owners are named; requested JPEG settings exist, but protocol/endpoint and
  observed behavior remain unverified.
- [x] Selenium remains disabled until the Phase 1 post-dedup coverage report
  demonstrates a target-class gap below 400.

## 2026-07-15 Current Status

- Phase 0 software skeleton, source pilots, manifest contracts, bounded queues,
  silent preview, exactly-once confirmation, and stale clearing have evidence.
- Gate B0 remains `NOT PASSED` only because the actual robot-camera frame and
  verified stream delivery contract are still open. The requested profile is
  480 x 480 JPEG quality 85 at 8 FPS, but it is not an observed stream result.
- Robot video is being handed over. Receipt alone is not a pass: verify consent,
  original dimensions, orientation/mirroring, color, source-frame identity,
  timestamps, freshness, and disconnect behavior before regenerating B0.
- Phase 1 acquisition produced a 2,321-item review handoff: 1,875 target and 446
  negative candidates at the latest recorded audit. Human filtering is in
  progress; accepted count was still zero, B1 is not passed, and no split may
  be frozen from pending rows.
- The official `B-D01` weight has a bounded non-robot GPU smoke: its `cat`
  mapping ran on all five assignment smoke images, with recorded local latency.
  Those images and crops remain training-excluded. No robot print-domain recall
  or time-saving claim exists until the handed-over video is evaluated.
- Detector-derived classifier crops have not been generated from the pending
  review pool. They must wait for human acceptance and split freeze; current
  2,321 pending rows cannot be used to create a training view manifest.

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
- Ensure `B-D01` remains annotation-free, classifier-only for species output,
  separately thresholded, bounded, optional, and centre-ROI fallback-safe.
- Ensure detector-derived views are generated after split, inherit parent/split,
  do not change base counts or sampling weight, retain misses, and exclude
  assignment/robot-test media.
- Ensure current data and robot handoff language distinguishes obtained,
  pending review, received, verified, accepted, and gate-passing states.
- Check local Markdown links, code fences, whitespace, `git diff --check`, and
  final status scope.

## Recorded-Video And Robot Validation

No physical motion. The offline consumer and deterministic skeleton exist, but
the robot-video handoff must still prove that at least one recorded or live
robot frame reaches the bounded UI/observation skeleton and exercise stale-frame
behavior. This documentation revision does not claim those runtime results.

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

### 2026-07-15 Refresh Validation

- Preserved the two remaining B0 failures instead of expanding or weakening
  the gate; completed software/source checks are now checked off and the robot
  frame/stream-contract items remain open.
- Recorded Phase 1 candidate acquisition and human-review status without
  treating pending rows as accepted images or freezing B1.
- Added the annotation-free `B-D01` design as a Phase 2 optional experiment,
  explicitly outside B0/B1 and unable to replace the centre-ROI release path.
- Matched the v1.3 model IDs, typed-boundary intent, no-console detector rule,
  bounded scheduling, fallback, video admission, and no-labeling stop rule.
- Rechecked local links, Markdown whitespace/fences, requirement immutability,
  architecture terms, `git diff --check`, and project-root status scope.

### 2026-07-15 Detector-Derived View Refresh Validation

- Kept human acceptance and grouped split freeze ahead of any crop generation;
  pending review rows remain ineligible for training views.
- Added parent/split inheritance, count exclusion, miss retention, per-class
  coverage, `not_target` routing, base-balanced sampling, deterministic
  validation crops, and assignment/robot-test exclusion.
- Added a one-view-per-parent materialization fallback so the derived-view
  design cannot block first training or silently double-weight detector hits.
- Updated localizer status from design-only to smoke-tested typed adapter/crop
  router while retaining disabled/not-release-admitted and no-robot-evidence
  status.
- Resolved owned links, parsed the Baseline YAML example, checked semantic
  guards and Markdown structure, and passed requirement immutability plus
  `git diff --check`.
