# Add A Pretrained Cat Localizer To The Baseline Plan

## Goal

Update the governing Baseline and its Phase 0 execution target for the agreed
two-stage assisted-localization design:

```text
COCO-pretrained cat detector -> padded candidate crop -> breed classifier
                                      |
                                      +-> centre-ROI fallback
```

The detector must require no project bounding-box annotation and must reduce
operator alignment effort without becoming a release dependency or changing
the five-breed classification contract. Record the current factual handoff
state: the candidate classification data has been obtained and is under manual
review, while robot video is still being transferred and has not been
validated.

## Dirty-State Decision

The worktree contains active Phase 0 implementation and handoff changes in
`README.md`, configuration, evaluation reports, scripts, tests, and two other
2026-07-15 targets. Those paths remain read-only. This target owns only the
high-level Baseline principle, the existing Phase 0 target, this plan, and the
maintenance log. It will not reinterpret existing readiness reports as proof
that the pending robot video has arrived.

## Owned Files

- `docs/plans/BASELINE_PLAN.md`
- `plan/2026-07-14-baseline-phase-0-foundation/plan.md`
- `plan/2026-07-15-add-pretrained-cat-localizer/plan.md`
- `plan/log.md`

## Read-Only Files And Directories

- `References/The requirement/**`
- `README.md`
- `AGENTS.md`
- `configs/**`
- `docs/evaluation/**`
- `scripts/**`
- `tests/**`
- `docs/plans/ADVANCED_PLAN.md` and Advanced dataset plans
- `plan/2026-07-15-activate-robot-jpeg-defaults/**`
- `plan/2026-07-15-build-minimal-review-handoff/**`
- all other existing target plans

## Dependencies

- Local NVIDIA RTX 4070.
- `B-M01`: pinned `yolo26s-cls.pt` classification checkpoint after training.
- `B-D01`: official COCO-pretrained `yolo26s.pt`, restricted to its `cat`
  output; `yolo26n.pt` is a latency fallback.
- Manually reviewed five-breed classification corpus and separate
  `not_target` candidates; raw data remains outside Git.
- Recorded robot video and stream facts from the Robotics team; currently in
  handoff, not yet accepted as validation evidence.

## Decisions

- `B-D01` is an annotation-free assisted localizer, not a breed recognizer and
  not an autonomous navigation component.
- The detector proposes cat-content boxes; `B-M01` alone decides the five
  reportable breeds or `not_target`.
- A detector miss immediately preserves the centre multi-scale ROI path. The
  official release must remain usable with `B-D01` disabled.
- Detector proposals are padded before classification and must pass freshness,
  size, blur, exposure, and temporal-stability gates.
- Detector and classifier confidence are thresholded and calibrated
  separately; raw scores are never multiplied as if they were comparable.
- Pretrained detector admission depends on same-video evidence that it reduces
  time-to-confirm without reducing the frozen classification/rejection gates.
- No detector fine-tuning or bounding-box annotation belongs to the current
  Baseline. Failure of the pretrained detector disables the enhancement rather
  than opening a new labeling workstream.

## Implementation Scope

This is a documentation/configuration-of-intent target only. It updates the
phase boundary, model table, runtime flow, data status, validation matrix, risk
controls, and Definition of Done. Model download, runtime code, threshold
sweeps, and video evaluation require later bounded implementation targets.

## Deterministic Validation

- Confirm the canonical classifier outputs and official 85/15 requirement are
  unchanged.
- Confirm the active classifier boundary remains unchanged and require the
  later `B-D01` implementation target to introduce its detector-specific typed
  observation with producer, crop-router consumer, and contract tests together;
  no framework-native object may cross into UI or scheduling code.
- Require fixtures for detector present/missing/stale, multiple candidates,
  padded crop bounds, centre-ROI fallback, no console output from detector,
  and bounded detector queues.
- Check model IDs, priorities, Gate definitions, local links, Markdown fences,
  whitespace, `git diff --check`, and final status scope.

## Recorded-Video Validation

After the pending robot video is accepted, compare on the same frozen clips:

- centre ROI plus classifier;
- pretrained detector crop plus classifier; and
- detector crop with centre-ROI fallback.

Record sequence-level localization success, false proposals, stale/missing
rate, time-to-first-stable-box, end-to-end time-to-confirm, FPS, and P95
latency. Until that evidence exists, `B-D01` remains disabled by default.

## Real Robot Motion

None. The localizer may draw boxes and operator guidance only; it never issues
motor commands.

## Commit Intent

Do not stage, commit, push, or open a pull request. Leave the bounded plan
changes for human review.

## Validation Results

- Confirmed `References/The requirement/**` is unchanged and the official five
  species, 85/15 split, live-camera, visible-output, remote-control, and
  no-autonomous-control contracts remain intact.
- Confirmed `B-M01` remains the sole species decision-maker and canonical
  classifier output; `B-D01` is optional, annotation-free, separately
  thresholded, centre-ROI fallback-safe, and disabled until same-video evidence
  exists.
- Confirmed the plans name official `yolo26s.pt`, its `yolo26n.pt` latency
  fallback, `Results.boxes` adaptation, bounded latest-only scheduling, padded
  crops, detector/classifier score separation, and no detector fine-tuning.
- Confirmed current-state language matches the existing evidence: 2,321 pending
  candidates (1,875 target and 446 negative) were under human review at the
  latest audit; B1 is not passed; robot video is in handoff; B0 remains open on
  a real frame and verified delivery contract.
- Resolved all 7 local links in the three owned plans; checked trailing
  whitespace, balanced code fences, required/obsolete terms, and model/Gate
  consistency. `git diff --check` passed.
- Reviewed final project-root status. Existing dirty handoff/config/report/code
  paths remained read-only; nothing was staged, committed, pushed, downloaded,
  trained, or executed against a robot by this target.
