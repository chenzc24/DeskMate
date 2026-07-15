# Code layout

`deskmate_baseline` is organized by responsibility. New implementation code
belongs in one of these packages:

```text
deskmate_baseline/
├── domain/       stable contracts, labels, manifests, and media metadata
├── data/         acquisition, review, preparation, and dataset splitting
├── perception/   detector/classifier adapters and ROI routing
├── app/          runtime orchestration and video inputs
└── experiments/  training, evaluation, and hardening workflows
```

Implementation modules live inside the responsibility-based packages. Import
them through their canonical path, for example:

```python
from deskmate_baseline.domain.contracts import FramePacket
from deskmate_baseline.perception.localization import route_classification_roi
```

## Dependency direction

- `domain` must not import from the other packages.
- `data` and `perception` may depend on `domain`.
- `experiments` may depend on `domain`, `data`, and `perception`.
- `app` composes the runtime-facing pieces and may depend on all lower layers.
- reusable logic belongs here; grouped files under `scripts/` are command
  entry points and should contain only argument parsing and orchestration as
  they are incrementally thinned.

Frozen datasets, checkpoints, reports, and reference material remain outside
the Python package and are not affected by this layout.
