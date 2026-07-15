# Maintenance Log

This log records accepted factual maintenance history for this project. Keep
reusable lessons in `docs/experience/`, not in this log.

Use concise entries:

```text
## YYYY-MM-DD - Target title

- Target: what the work set out to do.
- Changed areas: files, directories, or subsystems changed.
- Validation: commands or review performed.
- Commit status: committed, ready to commit, not committed, or blocked.
```

## 2026-07-14 - Correct Workflow Root To `/project`

- Target: correct the repository-boundary mistake so the current `/project` directory is the root for Agent rules, target plans, factual logs, experience notes, project entry documentation, and artifact policy.
- Changed areas: installed `AGENTS.md`, `README.md`, `.gitignore`, `plan/`, and `docs/experience/` under `/project`; removed the mistakenly installed parent kernel files; restored the containing repository README.
- Validation: checked all 9 owned paths, Markdown whitespace/fences, 5 local entry links, absence of parent kernel residue and nested `.git`, exact restoration of the parent README, and representative ignore rules. Full `git diff --check` was run and reported only pre-existing read-only whitespace in `../notes.md` and `BASELINE_PLAN.md`.
- Commit status: not committed; ready for user review. No file was staged or pushed.

## 2026-07-14 - Publish DeskMate As A Subrepository

- Target: publish the current `/project` tree as private repository `chenzc24/DeskMate`, then track it from `chenzc24/DeepLearning` as the `project` Git submodule.
- Changed areas: initialized the child repository, added its GitHub remote, prepared the complete project tree for the initial commit, and reserved the parent `.gitmodules` and `project` gitlink as the only parent-repository changes.
- Validation: reviewed the staged child file list and diff summary, ran `git diff --cached --check`, and scanned staged text files for common private-key and access-token signatures.
- Commit status: child initial commit `bd36ac0` and parent conversion commit `a67f845` were committed and pushed successfully. No pull request was requested or opened.

## 2026-07-14 - Structure Assignment Announcement

- Target: turn the copied Great Cat Census announcement into a readable Markdown handout without changing its requirements.
- Changed areas: `References/The requirement/Assignment announcement.md` and the target plan.
- Validation: confirmed the title and five required section headings; restored and checked the previously condensed logistics, mission narrative, team instructions, and evaluation content; checked that copied `Download` labels and the time-range encoding artifact were absent; and ran `git diff --check` plus `git status --short --branch`.
- Commit status: included in the user-requested consolidation of all pending project changes on `main`.

## 2026-07-14 - Split Formal Baseline And Advanced Plans

- Target: make the official five-breed Cat Census the only immediate P0 while preserving DeskMate as a post-Baseline Advanced project that reuses proven infrastructure.
- Changed areas: rewrote `BASELINE_PLAN.md`; added `ADVANCED_PLAN.md`; renamed the two desk-object dataset documents as Advanced-only; updated `README.md`, `AGENTS.md`, and the target plan.
- Validation: cross-checked all hard requirements against four local requirement transcriptions; checked seven Markdown files, 14 local links, code-fence balance, phase/model/date consistency, retention of all 17 original Advanced sections, obsolete active references, `git diff --check`, and final status scope.
- Commit status: not committed or pushed; ready for human review.

## 2026-07-14 - Organize High-Level Plans Under `docs/plans`

- Target: keep the repository root operational while grouping durable Baseline, Advanced, and Advanced-data principles under one documentation directory.
- Changed areas: moved four high-level documents to `docs/plans/`; added its index; updated root `AGENTS.md` and `README.md`; left formal originals under `References/The requirement/` unchanged.
- Validation: confirmed root/moved path state, resolved 20 active local links, checked requirement precedence in `AGENTS.md`, retained the Advanced phase section plus all 17 original numbered sections, and passed whitespace, code-fence, `git diff --check`, and status-scope checks.
- Commit status: not committed or pushed; ready for human review.

## 2026-07-14 - Revise Baseline To YOLO Classification And Stronger Redundancy

- Target: align Baseline/Advanced framework reuse without adding unrequired automatic detection, and raise the data/domain-test reliability target for the Cat Census.
- Changed areas: made `yolo26s-cls.pt` the Baseline primary and EfficientNet-B0 an evidence-gated backup; added multi-scale/multi-frame confirmation; raised data targets to 1,200/2,000/3,000 and the independent printed set to 50 base images; clarified `Results.probs` versus Advanced `Results.boxes` in `AGENTS.md`, `README.md`, and both phase plans.
- Validation: re-checked all formal task statements in four untouched requirement transcriptions; removed obsolete model and threshold decisions; confirmed active classification/detection schema separation and new data gates; resolved 20 local links; passed whitespace, code-fence, requirement-immutability, `git diff --check`, and scope checks.
- Commit status: not committed or pushed; ready for human review.

## 2026-07-14 - Freeze Baseline Phase 0 And Dataset-First Acquisition

- Target: divide the Baseline sprint into five gated execution phases and keep unrestricted image scraping out of the critical path while preserving it as measured gap-fill.
- Changed areas: `docs/plans/BASELINE_PLAN.md`, the Phase 0 target plan, and this maintenance log; added the five-class source matrix, manifest/provenance contract, source pilot, post-dedup Selenium go/no-go, and Phase 0–4 schedule.
- Validation: confirmed the formal requirement files are untouched; resolved all six active local links; checked canonical classes, data gates, 85/15 split, source/phase terms, code-fence balance, trailing whitespace, `git diff --check`, and final status scope.
- Commit status: not committed or pushed; ready for human review. No package was installed, scraper run, or dataset downloaded by this documentation target.

## 2026-07-14 - Harden Baseline Architecture And Model Selection

- Target: reduce live-demo false positives and data leakage while preserving a reusable engineering foundation for the later detection-based Advanced system.
- Changed areas: added an internal `not_target` rejection class, selection/calibration/final isolation, temperature calibration, quality-gated probability aggregation, bounded capture/preview/confirmation workers, a generic `ModelRunner[OutputT]` lifecycle with task-specific outputs, and evidence-gated Baseline/Advanced model challengers across `docs/plans/BASELINE_PLAN.md`, `docs/plans/ADVANCED_PLAN.md`, `AGENTS.md`, and `README.md`.
- Validation: confirmed the formal requirement files are untouched; re-checked the assignment contract; resolved 20 active local links; verified required and obsolete architecture terms, trailing whitespace, code-fence balance, `git diff --check`, and final status scope.
- Commit status: not committed or pushed; ready for human review.

## 2026-07-14 - Synchronize Phase 0 With Hardened Baseline

- Target: update the executable Phase 0 target after the Baseline v1.2 hardening without pulling training, calibration, or final evaluation into B0.
- Changed areas: synchronized `plan/2026-07-14-baseline-phase-0-foundation/plan.md` and this maintenance log; added the six-output order, grouped negative-source pilots, generic runner/task-output boundary, bounded worker fixtures, console-confirmation rule, and an explicit Gate B0 evidence checklist.
- Validation: confirmed requirement originals are unchanged; matched the hardened `not_target`, split, runner/output, queue, Selenium, and evaluation-isolation contracts; removed obsolete target wording; checked B0 phase ownership, Markdown whitespace/fences, `git diff --check`, and final status scope.
- Commit status: not committed or pushed; ready for human review. No package, dataset, model run, or robot motion was involved.

## 2026-07-14 - Execute Baseline Phase 0 And Audit Gate B0

- Target: implement the bounded Phase 0 software/data foundation, run traceable source pilots, and produce a fail-closed Gate B0 audit before any bulk acquisition or model training.
- Changed areas: added the `deskmate_baseline` contracts/runtime/manifest package, Phase 0 configuration, source-pilot and audit scripts, deterministic tests, data documentation/template, generated ignored pilot evidence, and human/machine-readable B0 reports.
- Validation: compilation passed; all 19 tests passed; the 60-row quarantine manifest passed with zero errors and warnings; the runtime smoke passed bounded-queue, silent-preview, exactly-once-confirmation, and stale-clearing checks; JSON/TOML parsing and `git diff --check` passed. Gate B0 was audited as `NOT_PASSED`: Oxford image pilot, representative `not_target` pilot, real robot-camera frame, and robot-stream contract remain open.
- Commit status: not committed or pushed. No training, Selenium run, bulk dataset acquisition, calibration, or robot motion was performed.

## 2026-07-14 - Complete Gate B0 Data Pilots

- Target: close the Oxford and representative `not_target` source-pilot gaps without accepting training data or weakening the fail-closed robot checks.
- Changed areas: extended source configuration and acquisition tooling with verified Oxford archive extraction and four grouped Commons negatives; regenerated ignored manifest/report/contact sheets; expanded review evidence, tests, and the B0 verifier; updated the human/machine-readable B0 reports.
- Validation: the official 791,918,971-byte Oxford archive hashed to `67195c5e1c01f1ab5f9b6a5d22b8c27a580d896ece458917e61d459337fa318d`; 13/13 groups produced 10 images; the 130-row quarantine manifest passed with zero errors/warnings; 20 tests and compilation passed; all 13 contact sheets were inspected. Gate B0 now fails only `real_robot_frame` and `robot_stream_contract`.
- Commit status: not committed or pushed. All images/archive remain ignored; no human acceptance, training, Selenium, calibration, or robot motion was performed.

## 2026-07-15 - Prepare Baseline Phase 1 Candidate Data

- Target: prepare a reproducible, traceable candidate pool and human-review queue while the user-deferred robot evidence remains open and without freezing Gate B1.
- Changed areas: added Phase 1 source/count configuration; cacheable Commons, Oxford, iNaturalist, and GBIF acquisition; deterministic technical filtering, SHA-256/dHash/original-URL deduplication; batched review sheets; dual-review and fail-closed review-audit tooling; tracked aggregate candidate reports.
- Validation: a cached full rerun combined 2,467 raw source rows into a 2,427-row manifest with zero audit errors/warnings; 2,321 candidates remain pending review (1,875 target and 446 negative); 39 same-ID aliases, one ID-label conflict, seven technical failures, two exact clusters, and 96 original-URL duplicate clusters were handled; 119 review sheets and a 2,321-row queue have zero missing files; all 31 tests and compilation pass. Accepted counts remain zero and no split is frozen.
- Commit status: not committed or pushed. Generated data remains ignored; no Selenium, human acceptance, training, calibration, robot access, or motion was performed.

## 2026-07-15 - Prepare Baseline Phase 2 Training Pipeline

- Target: make the reviewed-data-to-training path immediately runnable while keeping Gate B1 fail-closed on the pending human review and skipping user-deferred robot evidence.
- Changed areas: added deterministic grouped split and dataset-view tooling, pinned training configuration and dry-run entry point, a reproducible Python 3.12 CUDA environment recipe/lock, the official base-weight manifest, environment verification, tests, and Phase 2 readiness reports.
- Validation: both Python environments pass 38 tests; the bootstrap lock, CUDA tensor execution on the RTX 4070, official `yolo26s-cls.pt` size/SHA-256, classification-only smoke inference, TOML/YAML/JSON parsing, seven report checksums, and parent-directory launches pass. The real queue is refused with exit code 3 because all 2,321 rows remain pending.
- Commit status: not committed or pushed. No split was frozen and no official training, Selenium, calibration, robot connection, or motion was performed.

## 2026-07-15 - Prepare Baseline Phase 2 Inference Adapter

- Target: replace placeholder-only inference with a framework-contained Ultralytics classification adapter while refusing untrained or incorrectly mapped checkpoints.
- Changed areas: added fixed inference configuration, centre-ROI and six-class mapping logic, a full model-runner lifecycle, mapping/latency verification scripts, tests, and tracked inference-readiness evidence.
- Validation: both Python environments pass 48 tests; the real ImageNet base weight is rejected because it has 1,000 classes; 30 synchronized RTX 4070 smoke predictions measured 12.76 ms mean and 15.54 ms P95 raw inference; parsing, five checksums, B0/B1 fail-closed audits, requirement immutability, and diff checks pass.
- Commit status: not committed or pushed. Species output remains disabled until a fine-tuned checkpoint exists; no split, training, calibration, robot connection, or motion was performed.

## 2026-07-15 - Prepare Baseline Evaluation And Calibration

- Target: make post-training model selection, rejection evaluation, and temperature calibration deterministic and leak-resistant before real checkpoint predictions arrive.
- Changed areas: added evaluation configuration, a strict portable prediction schema, classification/rejection/NLL/ECE metrics, val-cal-only temperature fitting, an evaluation CLI, synthetic fixture, tests, and readiness reports.
- Validation: both Python environments pass 52 tests; a six-row fixture deterministically fitted temperature 1.65 and reduced fixture NLL from 1.37425 to 1.17300; parsing, four checksums, B0/B1 audits, requirement immutability, and diff checks pass.
- Commit status: not committed or pushed. Fixture metrics are not model evidence; no real calibration, threshold freeze, split, training, robot connection, or motion occurred.

## 2026-07-15 - Prepare Baseline Video Source And Offline Replay

- Target: make the video consumer ready for a future USB/file/URL endpoint while preserving fail-closed disconnect behavior and not inventing robot evidence.
- Changed areas: added a bounded OpenCV frame source, explicit health/reconnect counters, fake-capture tests, actual local MP4 replay smoke, and tracked readiness reports.
- Validation: both Python environments pass 55 tests; actual OpenCV wrote/read 20/20 320x240 BGR frames with sequential IDs, monotonic timestamps, EOF disconnect, and no stale reuse; parsing, checksums, B0/B1 audits, requirement immutability, and diff checks pass.
- Commit status: not committed or pushed. Replay is fixture-only; no robot endpoint, command, motion, split, training, or calibration was used.

## 2026-07-15 - Expose Phase 0 Manual Actions

- Target: make the remaining human work immediately actionable while preserving the distinction between Gate B0 robot evidence and Gate B1 image acceptance.
- Changed areas: added an operator-facing manual-action dashboard; linked it from the repository entry point and human-readable B0 audit; refreshed the machine-readable audit evidence; and documented this bounded target.
- Validation: system Python 3.13 and training Python 3.12 each pass all 55 tests; the B0 verifier remains fail-closed with exactly `real_robot_frame` and `robot_stream_contract` failed; the B1 auditor reports 2,321 pending, zero accepted, zero audit errors, and `ready_to_freeze_split=false`; JSON parsing, required-path checks, requirement immutability, and `git diff --check` pass.
- Commit status: the user authorized a bounded commit and push to `main`; no pull request is intended.

## 2026-07-15 - Build Minimal Phase 1 Review Handoff

- Target: hand the candidate pool to a colleague for human filtering without copying unrelated acquisition, training, inference, evaluation, video, or contact-sheet artifacts.
- Changed areas: added a concise reviewer README, a deterministic minimal-handoff builder, six safety/layout tests, and an ignored handoff containing the editable queue, integrity inventory, summary, and 2,321 candidate images flattened into one folder per class with no batch/source subdirectories.
- Validation: the image tree has exactly six class directories and zero nested directories; queue/inventory/image counts are all 2,321; 364,150,364 image bytes have zero missing, extra, or SHA-256-mismatched files; the 362,912,283-byte ZIP contains exactly 2,325 files and hashes to `5fa6a44804ed04e93f57d1b5c8342c9edb011bf081e1d400d4a4cc714cdb2af3`; both Python environments pass 61 tests and compilation; the copied queue audit intentionally remains fail-closed with 2,321 pending, zero accepted/rejected, zero errors, and `ready_to_freeze_split=false`.
- Commit status: not committed or pushed; generated data remains ignored. No acceptance decision, split freeze, training, robot connection, or motion occurred.

## 2026-07-15 - Activate Robot JPEG Defaults

- Target: restart robot integration with a provisional 480 x 480 JPEG quality 85 at 8 FPS profile while human image review proceeds independently.
- Changed areas: recorded the requested camera profile and latest-frame/freshness requirements; distinguished image encoding from the still-unknown delivery protocol and endpoint; refreshed B0 and video-readiness evidence; marked B1 human review in progress without claiming decisions.
- Validation: both Python environments pass all 61 currently discovered tests; B0 remains fail-closed only on the real robot frame and stream delivery contract; B1 reports 2,321 pending, zero accepted, zero audit errors, and `ready_to_freeze_split=false`.
- Commit status: not committed or pushed; the active untracked review-handoff paths remain untouched.

## 2026-07-15 - Add A Pretrained Cat Localizer To Baseline Planning

- Target: reduce operator alignment time without adding detector labeling or making localization a Baseline release dependency.
- Changed areas: updated `docs/plans/BASELINE_PLAN.md` and the Phase 0 target with optional official COCO `B-D01=yolo26s.pt` cat proposals, padded-crop routing into `B-M01`, bounded latest-only scheduling, centre-ROI fallback, same-video admission, and a no-fine-tuning stop rule; recorded the current image-review and robot-video handoff state.
- Validation: kept formal requirements untouched; confirmed classifier labels/outputs and B0/B1 gates are unchanged; resolved 7 local links; checked model IDs, current-state evidence, required/obsolete terms, Markdown whitespace/fences, `git diff --check`, and status scope.
- Commit status: not committed or pushed; ready for human review. Existing robot-JPEG, evaluation, handoff script, test, and report changes remained read-only.

## 2026-07-15 - Smoke Pretrained Cat Localizer During B1 Review

- Target: use the B1 human-review window for a bounded offline smoke of official COCO `B-D01=yolo26s.pt` without enabling it or changing the classifier and Gate contracts.
- Changed areas: added a pinned disabled localizer config, official weight manifest entry, typed box-only adapter, same-frame stable-box crop router with centre fallback, deterministic tests, GPU smoke script/report, and a Baseline timing clarification; the downloaded weight remains ignored.
- Validation: official 20,422,725-byte weight hashed to `646f8bc3fe0a656803d95c294f7852321748cb29d13466a1af8862e2db384a1b`; native `cat` resolved to ID 15; all five assignment smoke images produced a proposal; 25 warmed detector predictions measured 37.71 ms mean and 44.52 ms P95 on the RTX 4070; both Python environments pass 67 tests and compile checks; B0/B1 remain intentionally unchanged.
- Commit status: not committed or pushed. `B-D01` remains disabled and not release-admitted; no robot media, training, split freeze, species output, or motion was used.

## 2026-07-15 - Add Detector-Derived Classifier Views

- Target: align classifier training inputs with the optional runtime detector crops without detector annotation, split leakage, inflated image counts, detector-selection bias, or delayed first training.
- Changed areas: updated `docs/plans/BASELINE_PLAN.md` to v1.4 and refreshed the Phase 0 plan with review/dedup-before-split, split-before-derive, `view_manifest`, deterministic padded crops, parent-balanced original/crop sampling, miss retention, per-view evaluation, and a one-view-per-parent fallback; added the bounded target plan.
- Validation: preserved formal requirements and B0/B1 state; cross-checked the existing localizer smoke evidence; resolved 7 local links; parsed the YAML example; checked parent/split/count/miss/exclusion guards, model IDs, Markdown whitespace/fences, `git diff --check`, and status scope.
- Commit status: not committed or pushed; ready for human review. No crop was generated and all active localizer, review-handoff, robot-video, config, model-manifest, source, script, test, and evaluation paths remained read-only.

## 2026-07-15 - Process Human-Screened Cat Intake

- Target owner: `chenzc24`; execution agent: `Codex`.
- Target: turn the teammate-merged five-breed image delivery into a deterministic, auditable intake without modifying originals or claiming Gate B1 readiness.
- Changed areas: added canonical folder mapping, decode/dimension/hash checks, exact-duplicate exclusion, conservative dHash grouping, ignored clean-candidate materialization, tracked aggregate evaluation reports, tests, and the user-named target plan.
- Validation: all 2,427 images decode; 2,341 candidates remain after 79 below-floor and 7 redundant-exact exclusions; no cross-label exact duplicate exists; two independent scans have identical manifest/duplicate-review/audit hashes; both Python environments pass 71 tests; TOML/JSON parsing, compilation, and `git diff --check` pass.
- Commit status: not committed or pushed; generated data stays ignored. Gate B1 remains closed and no training, robot connection, or motion occurred.

## 2026-07-15 - Build Provisional Baseline Split

- Target: combine the processed human-screened five-breed intake with the original Phase 1 `not_target` pool under the user's explicit development-risk decisions, without changing official Gate B1.
- Changed areas: added a provisional dataset config, deterministic grouped split/materialization builder, tests, tracked aggregate evidence, and an ignored six-class 85/10/5 dataset view.
- Validation: 2,787 rows materialized with exact per-class rounded 85/10/5 allocation and zero source/duplicate/hash group leakage; every copy passed SHA-256; two independent builds match; both Python environments pass 74 tests; the official B1 audit remains fail-closed with exit 3.
- Commit policy: included in the user-authorized detector-view training code freeze. Provenance, source-session reconstruction, negative review, and cross-label dHash adjudication remain deferred development risks; no robot connection or motion occurred.

## 2026-07-15 - Freeze Detector-View Parallel-Training Handoff

- Target: implement the Baseline v1.4 `B-D01 -> B-M01` offline path and give two trainers identical data, code, dependencies, and pretrained weights for immediate classifier fine-tuning.
- Changed areas: generated a complete parent-linked detector-view manifest; materialized one deterministic crop-or-original view per parent; retargeted the guarded classifier training entry point; added a dataset-only handoff ZIP, Git-delivered training code, pinned asset bootstrap, inventories, tests, and evaluation evidence.
- Validation: pinned COCO `B-D01` generated 1,958 selected crops with 829 original/fallback views while preserving all 2,787 parents and the frozen 85/10/5 allocation; the clean repository extraction passed 2,789 dataset per-file size/SHA-256 checks, contained 2,787 training images and zero interrupted checkpoints, and passed the repository training dry-run.
- Commit policy: the user authorized this bounded code/configuration/evidence scope for direct commit and push to `main`; no PR. The interrupted original-only run is excluded and superseded. Gate B1 remains closed because negative review, provenance/license, source/session grouping, dHash adjudication, and multi-box review are still provisional; no robot connection or motion occurred.

## 2026-07-15 - Train Detector-View Baseline Classifier

- Target: train one real `B-M01` seed on the frozen one-view-per-parent outputs produced by `B-D01`, then independently reload and evaluate the best checkpoint.
- Result: patience-12 early stopping completed 19 epochs in 139.55 seconds; epoch 7 reached 95.71% val-select top-1 and 100% top-5, while an independent 280-image pass reproduced 95.71% accuracy and 95.81% macro F1.
- Checkpoint: `best.pt` is 11,035,778 bytes with SHA-256 `c41cfd4a12411883df52bf8643b20a2621b189bbd27c642bae441e92cf06319d`; canonical six-class mapping verified.
- Scope: development only and not committed automatically. Gate B1 remains false; val-cal, robot calibration, robot-final data, robot connection, and motion were not used.

## 2026-07-15 - Evaluate Robot-Camera Stills End To End

- Target: pass all three 640×480 frames in `data/downloads/Camera/` through the current `B-D01 -> padded crop/fallback -> B-M01 best.pt` chain and save visible evidence.
- Result: the active 2% area-floor config detected the near and medium images and classified both Sphynx at greater than 99.99% confidence; the far frame used centre fallback and returned `not_target` at 49.79% with only 16.43% margin.
- Diagnosis: the far frame had a native cat proposal at confidence 0.376 and area 1.26%, rejected solely by the 2% area floor. A diagnostic-only 1% floor produced a crop classified Sphynx at 99.13%; active thresholds remain unchanged pending a larger same-frame sweep with background negatives.
- Scope: no formal accuracy/FPS/P95 claim from three stills; no robot command, motion, commit, or push.

## 2026-07-15 - Re-evaluate Expanded Robot-Camera Still Batch

- Target: rerun the unchanged detector-to-classifier chain after new files arrived in `data/downloads/Camera/`, while preserving the first-batch artifacts.
- Result: the frozen snapshot contained six new images; four detector hits and two fallbacks produced four visible-label-correct outputs. Persian, Ragdoll, Persian, and Singapura were correct; both Pallas frames were predicted Persian.
- Diagnosis: one Pallas frame had an accepted detector crop but still failed classification; the second had only 0.0167 native detector confidence and failed all centre ROI scales. A 1% area-floor diagnostic recovered neither new miss, so the active configuration remains unchanged.
- Scope: results are descriptive from visible paper labels, not release accuracy evidence; no robot command, motion, commit, or push.

## 2026-07-15 - Review Detector Boxes On Original Data

- Target: show the user fresh `B-D01` boxes on a deterministic subset of immutable original target images without changing the frozen classifier dataset.
- Changed areas: added one user-scoped no-commit target and generated three ignored contact sheets plus CSV/JSON detector evidence under `data/downloads/baseline_detector_box_review/`; all concurrent training and robot-camera dirty paths remained read-only.
- Validation: fresh RTX 4070 inference used pinned detector SHA-256 `646f8bc3fe0a656803d95c294f7852321748cb29d13466a1af8862e2db384a1b`, Ultralytics 8.4.95, cat ID 15, `conf=0.25`, and `imgsz=640` on 40 original images. The deliberately biased sample yielded 20 hits, 9 multi-box results, and 11 misses; visual review exposed Sphynx/Pallas misses and multi-cat/nested-cat extra boxes. These are review counts, not detector accuracy.
- Commit status: no commit or push requested; generated sheets remain ignored and no robot motion occurred.

## 2026-07-15 - Review Full Pipeline On The Same Original Images

- Target: run the active detector crop/fallback and current provisional classifier checkpoint on exactly the same ordered 40-image detector-review sample.
- Changed areas: added one user-scoped no-commit target and generated three ignored full-pipeline contact sheets plus predictions CSV/JSON under `data/downloads/baseline_full_pipeline_review/`; all existing training, camera evaluation, data, and checkpoint paths remained read-only.
- Validation: both model hashes and the canonical class mapping passed; the same 40 parent IDs/paths/labels/order were asserted. The deliberately biased sample gave 37/40 top-1 correct, with detector crops 29/32 and centre fallbacks 8/8. Errors were one false Sphynx detector crop and two multi-box Singapura cases. Raw probabilities and sequential still-image latency are diagnostic only, not calibrated, temporal, held-out, or release evidence.
- Commit status: no commit or push; no threshold, dataset, checkpoint, robot command, or motion changed.

## 2026-07-15 - Validation-Only Full Pipeline Review

- Target: run the unchanged detector crop/fallback and classifier chain on every frozen `val_select` and `val_cal` parent, excluding train images.
- Changed areas: added one user-scoped no-commit target and generated ignored validation-only predictions/errors CSVs, JSON metrics, confusion matrix, and error/low-margin contact sheet under `data/downloads/baseline_full_pipeline_validation_only/`.
- Validation: 419 rows were asserted with zero train parents; overall raw top-1 was 398/419 (94.99%), target-only 339/352 (96.31%), provisional-negative rejection 59/67 (88.06%), macro-F1 0.9511; `val_select` was 267/280 and `val_cal` 131/139. Detector crops were 276/293 and fallbacks 122/126. Sequential static chain measured 51.54 ms mean/64.21 ms P95. These are validation diagnostics, not final calibration or robot-domain release metrics.
- Commit status: no commit or push; no source, split, threshold, model, checkpoint, robot command, or motion changed.

## 2026-07-15 - Expand Full-Pipeline Static Diagnostic To 600 Images

- Target: expand the unchanged detector-crop/fallback-to-classifier review to 600 unique original parents, balanced at 100 per target/rejection class and 85/10/5 per-class split, while excluding the preceding 40.
- Changed areas: added one user-scoped no-commit target and generated ignored predictions/errors CSVs, JSON metrics, confusion matrix, and balanced/failure/low-margin/fallback sheets under `data/downloads/baseline_full_pipeline_expanded/`; concurrent training and camera-evaluation work remained read-only.
- Validation: model hashes, source existence, sample uniqueness/distribution, schemas, counts, and image decoding passed. The mixed-split diagnostic yielded 588/600 correct, 98.4% target-only accuracy, 96% provisional-negative rejection, macro F1 0.9800, detector-crop 401/409, fallback 187/191, and warmed sequential static chain 49.32 ms mean/55.62 ms P95. These are not held-out, temporal, camera, or release metrics.
- Commit status: no commit or push; no source, split, threshold, model, checkpoint, robot command, or motion changed.

## 2026-07-15 - Harden Detector-To-Classifier ROI Routing

- Target: prevent implausibly small detector crops from suppressing centre fallback, recover useful 1%-area cat proposals, and remove near-duplicate candidates without treating routing as a cure for breed/domain errors.
- Changed areas: added a 64-source-pixel padded-crop gate, explicit fallback reasons, IoU 0.85 candidate de-duplication, a 1% detector area floor, unit tests, a reproducible four-policy ablation, and tracked aggregate evidence; generated per-image results and the robot comparison sheet remain ignored.
- Validation: 10 targeted tests passed; the control reproduced all 640 previous non-robot predictions. Hardened routing moved the biased 40 from 37 to 38 correct and the nine robot stills from 6 to 7 visible-label-correct, with no change across the expanded 600 and zero observed regressions. Candidate de-duplication reduced 12 candidate sets without changing top routes. A robot-only confidence `[0.01, 0.25)` sweep added four candidates but classified none correctly, including both Pallas proposals as Persian; Pallas remains explicitly deferred to a separate classifier/domain-data target.
- Commit status: user explicitly authorized a bounded direct commit and push to `main`; results remain static diagnostics, not held-out release accuracy; no robot command or motion occurred. Concurrent dirty paths remain unstaged.
