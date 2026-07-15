# Command layout

Commands are grouped by the workflow they operate:

```text
scripts/
├── data/        acquire, audit, prepare, review, and freeze datasets
├── training/    train models and compose checkpoints
├── evaluation/  benchmark, compare, verify, and visualize predictions
├── runtime/     run offline or robot-facing smoke paths
└── tools/       manage environments, assets, inventory, and handoffs
```

Run commands from the repository root. For example:

```powershell
.\.venv\Scripts\python.exe scripts\training\train_provisional_baseline.py
.\.venv\Scripts\python.exe scripts\evaluation\compare_baseline_routing.py
```

Reusable implementation belongs under `src/deskmate_baseline/`; command files
should focus on argument parsing, filesystem orchestration, and reporting.
