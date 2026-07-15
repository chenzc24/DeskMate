"""Freeze the dataset archive used for parallel B-M01 fine-tuning."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
FIXED_ZIP_TIME = (2026, 7, 15, 0, 0, 0)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inventory(files: Iterable[tuple[Path, str]]) -> list[dict[str, Any]]:
    rows = []
    for source, archive_path in sorted(files, key=lambda item: item[1]):
        if not source.is_file():
            raise FileNotFoundError(source)
        rows.append(
            {
                "path": archive_path.replace("\\", "/"),
                "bytes": source.stat().st_size,
                "sha256": sha256_file(source),
            }
        )
    if len({row["path"] for row in rows}) != len(rows):
        raise ValueError("archive inventory contains duplicate paths")
    return rows


def write_deterministic_zip(
    path: Path,
    files: list[tuple[Path, str]],
    generated_entries: dict[str, bytes] | None = None,
) -> None:
    generated_entries = generated_entries or {}
    names = [name.replace("\\", "/") for _, name in files] + list(generated_entries)
    if len(set(names)) != len(names):
        raise ValueError("duplicate archive member")
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for source, archive_path in sorted(files, key=lambda item: item[1]):
            info = zipfile.ZipInfo(archive_path.replace("\\", "/"), FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes())
        for archive_path, data in sorted(generated_entries.items()):
            info = zipfile.ZipInfo(archive_path, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)


def data_files(derived_root: Path) -> list[tuple[Path, str]]:
    prefix = Path("data/downloads/baseline_detector_views")
    selected = [
        derived_root / "view_manifest.csv",
        derived_root / "derived_view_report.json",
    ]
    selected.extend(
        path
        for path in (derived_root / "one_view_yolo_classify").rglob("*")
        if path.is_file()
    )
    return [
        (source, (prefix / source.relative_to(derived_root)).as_posix())
        for source in selected
    ]


def readme_text() -> str:
    return """# DeskMate Baseline Parallel Fine-Tuning Handoff

Code is delivered through the DeskMate Git repository. Pull the frozen commit,
then extract the dataset ZIP at the repository root. The extracted tree already
contains one detector-derived-or-original view per frozen parent; do not run
detection again before the first comparison runs.

The detector is `B-D01=yolo26s.pt`, a frozen COCO cat localizer. It generated
the padded classifier views but is not fine-tuned and never predicts breed.
The model being fine-tuned is `B-M01=yolo26s-cls.pt` with six classification
outputs: ragdoll, singapura, persian, sphynx, pallas, not_target.

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap_training_env.ps1
.\\.venv\\Scripts\\python.exe scripts/train_provisional_baseline.py
.\\.venv\\Scripts\\python.exe scripts/train_provisional_baseline.py --execute
```

Bootstrap downloads the pinned official classifier base weight and verifies its
SHA-256. The first Python command is a checksum/layout dry run. Run `--execute`
only after it succeeds. Independent comparison runs may keep the same seed when
they are on separate machines; use distinct run directories only if outputs
share storage. Runs are development-only because official B1 review/provenance
is not frozen.
"""


def freeze(output_dir: Path, derived_root: Path) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"handoff output already exists: {output_dir}")
    report_path = derived_root / "derived_view_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("status") != "DETECTOR_DERIVED_ONE_VIEW_DATASET_READY":
        raise RuntimeError("derived dataset is not ready")
    if report.get("selected_view_count") != report.get("parent_count"):
        raise RuntimeError("derived dataset is not one-view-per-parent")
    output_dir.mkdir(parents=True)
    data_archive = output_dir / "deskmate_baseline_data_bd01_views_20260715.zip"
    data_members = data_files(derived_root)
    data_inventory = inventory(data_members)
    readme = readme_text().encode("utf-8")
    write_deterministic_zip(
        data_archive,
        data_members,
        {"FROZEN_DATA_INVENTORY.json": (json.dumps(data_inventory, indent=2, sort_keys=True) + "\n").encode("utf-8")},
    )
    summary = {
        "schema_version": 2,
        "freeze_id": "deskmate-baseline-bd01-views-20260715-v2",
        "scope": "development_only_not_final_release",
        "code_delivery": "git_repository",
        "weight_delivery": "pinned_manifest_download_during_bootstrap",
        "official_gate_b1_ready": False,
        "parent_count": report["parent_count"],
        "selected_view_count": report["selected_view_count"],
        "view_manifest_sha256": report["view_manifest_sha256"],
        "data_archive": {
            "file": data_archive.name,
            "bytes": data_archive.stat().st_size,
            "sha256": sha256_file(data_archive),
            "members": len(data_members) + 1,
        },
        "excluded": [
            "interrupted training run and checkpoints",
            "raw acquisition caches",
            "unselected original/crop files",
            "robot media and assignment examples",
        ],
    }
    (output_dir / "FREEZE_SUMMARY.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "SHA256SUMS.txt").write_text(
        f"{summary['data_archive']['sha256']}  {data_archive.name}\n",
        encoding="utf-8",
    )
    (output_dir / "README_FINE_TUNE.md").write_bytes(readme)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--derived-root",
        type=Path,
        default=ROOT / "data" / "downloads" / "baseline_detector_views",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "data" / "downloads" / "baseline_training_handoff_20260715",
    )
    args = parser.parse_args()
    result = freeze(args.output_dir, args.derived_root)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
