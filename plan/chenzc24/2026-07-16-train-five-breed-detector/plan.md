# Train and compare the five-breed detector

## Outcome and owned paths

Build one reproducible five-breed YOLO detector view from the frozen BD05
Sphynx/Pallas data and the returned Ragdoll/Singapura/Persian annotations,
apply the existing screen/print augmentation to train positives only, train a
new detector from the pinned COCO checkpoint, and compare it with BD05 on the
same 24-image detector-to-M9 diagnostic.

Owned tracked paths:

- `scripts/data/build_five_breed_detector_dataset.py`
- `scripts/data/build_screenprint_detector_augmentation.py`
- `scripts/evaluation/evaluate_robot_target5.py`
- `tests/test_five_breed_detector_dataset.py`
- `tests/test_screenprint_detector_augmentation.py`
- `docs/evaluation/BASELINE_FIVE_BREED_DETECTOR_20260716.md`
- `models/manifest.yaml` and a frozen BD06 record only if the candidate passes
- `.gitignore` only for the narrow `models/frozen/*.json|*.toml` tracking rule
- this plan and one factual entry in `plan/log.md`

Ignored/generated paths:

- `data/work/detector-five-breed-base-20260716/`
- `data/work/detector-five-breed-screenprint-20260716/`
- `runs/detector_tuner/bd06-five-breed-screenprint-from-pretrained-s20260715-20260716/`
- `artifacts/bd06-five-breed-evaluation-20260716/`

## Dirty paths left read-only

Preserve the pre-existing `.gitignore` presentation-showcase addition,
`plan/log.md`, presentation-showcase script/test, and the two 2026-07-16
handoff/showcase plan directories except for the narrow model-record ignore
rule above and appending this target's completed factual log entry at the end.

## Dependencies

- frozen BD05 base data and background negatives under `data/downloads/`
- returned three-breed YOLO data under
  `data/downloads/ultralytics_yolo_detection/`
- `models/yolo26s.pt`, frozen M9, RTX 4070, OpenCV, Ultralytics, Pillow

## Validation and robot motion

- validate every image/label pair, class, box, hash, split, and source overlap;
- run targeted tests and the practical full pytest suite;
- train from `models/yolo26s.pt` with deterministic seed `20260715`;
- evaluate BD05 and BD06 with frozen M9 and identical 24-image routing;
- record dataset/checkpoint hashes, detector validation metrics, per-frame
  transitions, latency, and the limitations of the correlated diagnostic set;
- no robot connection or motion is involved.

## Commit intent

Do not commit or push unless the user explicitly asks after reviewing the
result. Keep large media, datasets, runs, and checkpoints outside Git until a
candidate is explicitly promoted.
