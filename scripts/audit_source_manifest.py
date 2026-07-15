"""CLI for the framework-neutral Baseline source-manifest auditor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from deskmate_baseline.manifest import audit_manifest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--target-per-class", type=int, default=400)
    parser.add_argument("--review-buffer", type=float, default=1.25)
    parser.add_argument("--not-target-floor", type=int, default=300)
    args = parser.parse_args()
    report = audit_manifest(
        args.manifest,
        target_per_class=args.target_per_class,
        review_buffer=args.review_buffer,
        not_target_floor=args.not_target_floor,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
