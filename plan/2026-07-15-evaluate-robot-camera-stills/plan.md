# Evaluate Robot-Camera Stills Through Detector And Classifier

## Goal

Run the three JPG/PNG frames under `data/downloads/Camera/` through the current
`B-D01 -> padded ROI -> B-M01 best.pt` chain, save auditable annotated outputs,
and report predictions and latency without claiming accuracy in the absence of
an explicit ground-truth manifest.

## Owned Files And Directories

- `artifacts/robot_camera_eval/` (ignored/generated)
- `.gitignore`
- `docs/evaluation/BASELINE_ROBOT_CAMERA_STILLS.json`
- `docs/evaluation/BASELINE_ROBOT_CAMERA_STILLS.md`
- `docs/evaluation/BASELINE_ROBOT_CAMERA_BATCH2.json`
- `docs/evaluation/BASELINE_ROBOT_CAMERA_BATCH2.md`
- `plan/2026-07-15-evaluate-robot-camera-stills/plan.md`
- `plan/log.md` (append only)

## Read-Only Paths

- `data/downloads/Camera/` input frames
- detector/classifier weights, configs, frozen training data, and training run
- requirement originals, Gate B1, robot protocol, and Advanced paths

## Dependencies And Assumptions

- Pinned `B-D01=yolo26s.pt`, COCO `cat` ID 15, `imgsz=640`, confidence 0.25,
  minimum box area 0.02, and padding 0.15.
- Current provisional `B-M01` best checkpoint with its verified six-class map.
- A detector box in a single still is treated as usable for visualization;
  still images cannot prove the live temporal-stability gate.
- If no usable cat box exists, use the configured 0.8 centre ROI and mark the
  result as fallback rather than silently treating it as a detector hit.

## Validation

- Decode all input images without modifying them.
- Record detector count/box/confidence, routed pixel ROI, top-3 classifier
  output, margin, and component/end-to-end latency for every frame.
- Save one annotated image and routed crop per input plus a contact sheet.
- Verify output counts, JSON parsing, model/checkpoint hashes,
  `git diff --check`, and scoped status.

## Robot Motion

No robot connection or motion is involved; only already-captured frames are
read.

## Commit Intent

No commit or push was requested for this evaluation target.

## Outcome

- Decoded all three 640×480 frames and saved three active-config annotations,
  three routed ROIs, a contact sheet, CSV, and full JSON evidence.
- Active configuration detected two frames and classified both as Sphynx; the
  far frame fell back and returned `not_target` with low margin.
- Low-threshold inspection proved that the far image had a 0.376-confidence cat
  proposal covering 1.26% of the frame, filtered only by the active 2% area
  floor.
- A diagnostic 1% area-floor route classified the far crop as Sphynx with
  99.13% confidence. No active configuration was changed from three stills.

## Batch 2 Outcome

- Re-froze the folder at nine images: three previous plus six new 640×480
  frames. Two additional filenames seen during upload were absent from the
  evaluated filesystem snapshot.
- Active routing detected four of six new frames. Visible-label inspection gave
  four correct results: Persian, Ragdoll, Persian, and Singapura.
- Both visible Pallas frames were predicted Persian. One had a valid detector
  crop, proving a classifier/domain failure; the other had only 0.0167 detector
  confidence and also failed all centre ROI scales.
- Lowering only the detector area floor to 1% recovered neither new miss. No
  active model or threshold was changed.
