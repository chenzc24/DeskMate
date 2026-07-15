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
