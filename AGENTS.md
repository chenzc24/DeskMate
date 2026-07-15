# DeskMate Repository Rules

This directory is the DeskMate project root. Keep the workflow small: one
source of truth per artifact type, one bounded target at a time, and no copied
datasets or checkpoints without a clear reason.

## Authority And Scope

1. `References/The requirement/` is read-only and overrides project documents.
2. `docs/plans/BASELINE_PLAN.md` governs until Baseline Gate B4 passes.
3. `docs/plans/ADVANCED_PLAN.md` governs only after the Baseline release is
   frozen.
4. A dated target plan may bound implementation work but may not weaken the
   authorities above.

Do not modify the containing course workspace unless the user explicitly names
it. Preserve unrelated dirty files. Never commit, push, create a branch, or
open a PR unless the user asks.

## Minimal Target Workflow

For code, data, model, protocol, or multi-file changes, create or update one
plan at `plan/<git-user>/<YYYY-MM-DD-target>/plan.md`. State only:

- outcome and owned paths;
- dirty paths left read-only;
- external data/model/hardware dependencies;
- validation and whether robot motion is involved;
- commit intent.

Do not create extra policy documents, experience notes, or overlapping plans
unless a human requests them. Record factual completed validation once in
`plan/log.md`.

## Artifact Ownership

Git is the control plane; large binaries stay local or in an artifact store.

| Artifact | Canonical location | Git policy | Lifetime |
| --- | --- | --- | --- |
| source/review/split manifests | `data/manifests/` | tracked | permanent |
| downloaded/raw media | `data/raw/` or legacy `data/downloads/` | ignored | keep one canonical copy |
| derived training views | `data/work/<dataset-id>/` | ignored | reproducible and disposable |
| training runs | `runs/<run-id>/` | ignored | temporary workspace |
| model metadata | `models/manifest.yaml` | tracked | permanent |
| model weights | `models/` or artifact store | ignored | retain only admitted versions |
| detailed runtime evidence | `artifacts/` | ignored | retain only when needed |
| compact evaluation summary | `docs/evaluation/` | tracked | permanent |

Existing paths under `data/downloads/` remain valid while active experiments
use them. New pipelines must not create another full copy merely to rename,
verify determinism, or hand data to a run. Generate temporary views, compare
their manifests/hashes, then remove them.

## Dataset Rules

- Identify a dataset snapshot by its manifest SHA-256, not its directory name.
- Keep original bytes immutable and store one row per source item with license,
  source/session group, label, and content hash.
- Split reviewed base images before generating crops or augmentations. Keep all
  duplicate, near-duplicate, and video-session relatives in one split.
- The Baseline target split is 85% train, 10% model selection, and 5%
  calibration. Assignment examples never enter training or evaluation.
- Derived views must carry parent image ID, split, transform, and producing
  model/config hash. They are cache, not new independent data.
- Never delete a canonical source or frozen manifest until a verified second
  copy exists. Never commit private media or personal data.

## Experiment And Model Rules

Use one immutable run ID:

```text
<stage>-<dataset-id>-<model>-s<seed>-<YYYYMMDD-HHMM>
```

Every meaningful run records the Git commit/dirty state, resolved config,
dataset and view-manifest hashes, base-weight hash, seed, environment, metrics,
and produced checkpoint hash. A directory name alone is not provenance.

- `runs/` is scratch space, never the permanent release registry.
- Keep metrics/configs for useful comparisons. Keep `last.pt` only while resume
  is plausible; keep `best.pt` only for active candidates.
- Failed-run weights and unselected soup weights are disposable after their
  metrics and recipe are recorded.
- Promote a model by adding an immutable version and SHA-256 to
  `models/manifest.yaml`. Release/fallback configs must resolve through that
  manifest, not an arbitrary mutable `runs/...` path.
- States are `development`, `candidate`, `release`, or `fallback`. Only one
  release and one fallback per model ID may be active.
- Run `python scripts/tools/artifact_inventory.py` before cleanup or promotion. It is
  read-only; cleanup remains an explicit human-approved action.

## Baseline Architecture Invariants

- One active `yolo26s-cls.pt` classifier produces five reportable breeds plus
  internal `not_target`; it uses `Results.probs`, not detection boxes.
- Preserve `FramePacket -> ModelRunner[ClassificationObservation]`. Framework
  tensors/results never cross into UI, logging, or control code.
- Frames must pass freshness, blur, exposure, and ROI gates. Missing/stale data
  clears temporal state; `unknown` is never treated as zero evidence.
- Preview, confirmation, capture, and UI queues stay bounded. Only confirmed
  target species are printed.
- Baseline DL never sends motor commands. Advanced experts never bypass the FSM
  safety gate.

## Validation

Always run `git diff --check` and scoped `git status --short --branch`.

- Documentation/config: parse machine-readable files and check referenced
  paths, IDs, hashes, labels, and gates.
- Python: targeted tests plus `python -m pytest -q tests` when practical.
- Model/data: record the exact dataset/view/checkpoint hashes and compare on the
  same held-out evidence.
- Perception: use recorded robot-view evidence and report validity, stale/miss
  rate, throughput, and P95 latency; do not infer performance from code.
- Robot motion: mock/protocol tests first; physical motion requires an operator,
  clear area, low speed, collision protection, watchdog, and emergency stop.

Downloaded data, weights, runs, videos, logs, secrets, signed URLs, and local
environments must remain outside Git. The final demo must load required assets
offline.
