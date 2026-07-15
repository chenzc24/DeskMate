# Revise Baseline To YOLO Classification And Stronger Redundancy

## Goal

Update the official Baseline principles after re-reading the assignment:

- use Ultralytics YOLO26 classification, not object detection, as the primary
  five-breed model;
- reuse the Ultralytics/PyTorch deployment toolchain in Advanced without
  pretending that classification weights, heads, labels, or datasets transfer
  to object detection;
- increase clean-data and target-domain evidence beyond the assignment's
  approximate 1,000-image suggestion; and
- make operator-guided alignment, multi-scale crops, multi-frame consensus, and
  visible output the robust path instead of autonomous search or alignment.

## Dirty-State Note

The worktree already contains the uncommitted Baseline/Advanced split and the
move of high-level plans into `docs/plans/`. Those owned changes remain in
scope. This target changes only their model/data/redundancy decisions.

## Owned Files

- `docs/plans/BASELINE_PLAN.md`
- `docs/plans/ADVANCED_PLAN.md`
- `README.md`
- `AGENTS.md`
- `plan/log.md`
- This target plan.

## Read-Only Files

- `References/The requirement/**` — authoritative evidence.
- `docs/plans/ADVANCED_DATASET_*.md` — Advanced desk-object data decisions are
  unaffected.
- Source scripts, prior target plans, and experience notes.

## Decisions

- Primary `B-M01`: `yolo26s-cls.pt`, ImageNet-pretrained, five-class whole-ROI
  classification through the official Ultralytics classify task.
- Fallback `B-M01F`: Torchvision EfficientNet-B0, trained only after the primary
  live pipeline works or if the primary misses the model gate.
- No Baseline bounding-box labels and no trained detector unless real robot
  rehearsals prove operator-guided multi-scale ROI classification insufficient.
- Data: release floor 1,200 clean unique images, target 2,000, stretch 3,000;
  keep the required 85/15 split.
- Domain test: 50 unseen base images, 10 per class, printed and captured through
  the real robot camera under multiple conditions without counting repeated
  frames as unique images.

## Validation

- Cross-check remote-control, non-autonomous navigation, eight images, live
  model output, console visibility, five classes, 85/15 split, and approximate
  1,000-image guidance against the four requirement transcriptions.
- Confirm every active document distinguishes YOLO classification (`probs`) from
  Advanced detection (`boxes`).
- Confirm all old 1,100/1,250/25-image release targets and EfficientNet-primary
  statements are removed from active principles.
- Resolve active Markdown links and run whitespace, fence, `git diff --check`,
  and final scope checks.

## Validation Results

- Re-checked all required task statements in the four untouched requirement
  transcriptions: remote control, no autonomous-navigation requirement, eight
  images, live feed, visible console output, five classes, 85/15 split, transfer
  learning, and the approximate 1,000-image guidance.
- Confirmed active principles consistently use `yolo26s-cls.pt` with
  `Results.probs` for Baseline and `yolo26n.pt` with `Results.boxes` for
  Advanced; obsolete EfficientNet-primary and old data/test thresholds are gone.
- Confirmed the 1,200 floor, 2,000 target, 3,000 stretch, 50-base-image domain
  test, and 46/50 gate are present in active principles.
- Resolved 20 active local Markdown links; whitespace, code-fence,
  `git diff --check`, requirement immutability, and scope checks passed.

## Real Robot Motion

None. Documentation only. Later tests remain remotely operated.

## Commit Intent

Do not commit or push automatically; leave the combined plan changes for human
review.
