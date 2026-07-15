# Baseline Phase 2 Training Readiness

Status: **pipeline ready; Gate B0/B1 evidence still pending**.

The non-blocked Phase 2 preparation is complete. The repository can now merge
an approved review queue, freeze a deterministic group-aware 85/10/5 split,
materialize the Ultralytics classification directory view, and generate the
first `B-M01` training run without changing code. It deliberately refuses to
do any of those irreversible data steps while all 2,321 candidates remain
pending human review.

## Ready Components

- Review decisions are merged fail-closed. Singapura, Pallas, and Persian
  require distinct agreeing second reviewers.
- Source/session groups, duplicate clusters, and identical file hashes are
  unioned before deterministic allocation with seed `20260714`.
- The generated view uses indexed class directories (`0_ragdoll` through
  `5_not_target`) so Ultralytics `ImageFolder` ordering cannot silently change
  the canonical output order.
- Materialization prefers hard links, verifies every SHA-256, is idempotent,
  and rejects untracked extra files.
- Training defaults to a dry run. Actual execution additionally requires a
  machine-readable Gate B1 report with `ready=true`, a materialized train/val
  view, and the verified base weight.
- A project-local Python 3.12 environment is pinned and reproducible through
  `scripts/bootstrap_training_env.ps1` and the tracked dependency lock.

## Verified Local Stack

| Item | Verified value |
| --- | --- |
| Training Python | 3.12.10 (`.venv`) |
| PyTorch | 2.11.0+cu128 |
| Torchvision | 0.26.0+cu128 |
| Ultralytics | 8.4.95 |
| CUDA runtime | 12.8 |
| GPU | NVIDIA GeForce RTX 4070 Laptop GPU |
| Base model | `yolo26s-cls.pt`, 13,622,082 bytes |
| Base-model SHA-256 | `816790029d5df3fef358f03c8144b96339d8824ee25577aeda8be0963e5c5f09` |

The official base model loaded on the GPU and returned `Results.probs` with no
detection boxes. Its ImageNet output on one assignment example was
`Persian_cat`; that proves only model loading and classification-task wiring.
The example is absent from the training manifest, and this smoke result is not
Cat Census accuracy evidence.

Ultralytics documents `yolo26s-cls.pt` as an ImageNet-pretrained YOLO26
classification model. The tracked manifest records the official release URL,
checksum, environment, input/output contract, and AGPL-3.0 license. Academic
coursework is listed by Ultralytics as a typical AGPL use, but the team must
review the license before closed-source or commercial distribution.

## Gates Still Open

| Gate | State | Remaining evidence |
| --- | --- | --- |
| B0 | Deferred by user | Real robot frame and stream contract |
| B1 | Not passed | 2,321 human decisions; accepted count is still zero |
| B2 | Not started | Fine-tuned checkpoint and real live-stream integration |

Running `scripts/freeze_baseline_split.py` against the current queue exits with
code 3 and writes no split. Running `scripts/train_baseline.py` without
`--execute` produces the pinned dry-run plan. No official training, split
freeze, robot connection, Selenium acquisition, calibration, or motion was
performed.

## Validation

- 38 deterministic tests pass in both the default development environment and
  the pinned training environment.
- CUDA tensor execution, core-version checks, model size/checksum, and one
  classification smoke inference pass.
- Gate B0 still fails only the two intentionally deferred robot checks.
- Requirement originals are read-only and unchanged.
