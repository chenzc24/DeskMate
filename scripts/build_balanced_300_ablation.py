from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LABELS = ("0_ragdoll", "1_singapura", "2_persian", "3_sphynx", "4_pallas", "5_not_target")
TARGETS = set(LABELS[:-1])
TARGET_COUNTS = {"train": 255, "val": 30, "val_cal": 15}


def ranked(files: list[Path], seed: int) -> list[Path]:
    return sorted(files, key=lambda p: hashlib.sha256(f"{seed}:{p.name}".encode()).hexdigest())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260715)
    args = parser.parse_args()
    source = args.source if args.source.is_absolute() else ROOT / args.source
    output = args.output if args.output.is_absolute() else ROOT / args.output
    if output.exists():
        raise FileExistsError(output)
    counts: dict[str, dict[str, int]] = {}
    manifest_rows: list[dict[str, str]] = []
    split_seed = {"train": 11, "val": 22, "val_cal": 33}
    for split in ("train", "val", "val_cal"):
        counts[split] = {}
        for label in LABELS:
            files = [p for p in (source / split / label).glob("*") if p.is_file()]
            if label in TARGETS:
                desired = TARGET_COUNTS[split]
                if len(files) < desired:
                    # Singapura has 253 train images in the user's current handoff;
                    # retain all available unique files rather than duplicate them.
                    if label not in {"1_singapura", "4_pallas"} or len(files) < desired - 10:
                        raise RuntimeError(f"{split}/{label}: need {desired}, got {len(files)}")
                    desired = len(files)
                files = ranked(files, args.seed + split_seed[split])[:desired]
            else:
                files = ranked(files, args.seed)
            dest = output / split / label
            dest.mkdir(parents=True, exist_ok=True)
            for file in files:
                shutil.copy2(file, dest / file.name)
                manifest_rows.append({"split": split, "label": label, "path": (Path(split) / label / file.name).as_posix()})
            counts[split][label] = len(files)
    if any("other_cat" in name.name.lower() for name in (output / "train" / "5_not_target").iterdir()):
        raise RuntimeError("other-cat negative remains in balanced dataset")
    manifest = output / "balanced300_split_manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["split", "label", "path"])
        writer.writeheader()
        writer.writerows(manifest_rows)
    manifest_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
    report = {
        "schema_version": 1,
        "seed": args.seed,
        "source": str(source),
        "counts": counts,
        "manifest_sha256": manifest_sha,
        "provisional_training_data_ready": True,
        "official_gate_b1_ready": False,
        "risk_scope": "development_only_not_final_release",
    }
    (output / "balanced300_split_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / "BALANCED300_DATASET_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
