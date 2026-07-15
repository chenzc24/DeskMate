"""Fetch pinned Baseline model assets declared in the tracked manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, BinaryIO, Callable
from urllib.request import urlopen

import yaml


ROOT = Path(__file__).resolve().parents[1]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_asset(
    root: Path,
    entry: dict[str, Any],
    *,
    opener: Callable[..., BinaryIO] = urlopen,
) -> dict[str, Any]:
    destination = root / entry["file"]
    expected_hash = str(entry["sha256"]).lower()
    expected_bytes = int(entry["bytes"])
    if destination.is_file():
        actual_hash = sha256_file(destination)
        if destination.stat().st_size == expected_bytes and actual_hash == expected_hash:
            return {"id": entry["id"], "path": entry["file"], "state": "already_verified"}
        raise RuntimeError(f"existing model asset failed checksum: {destination}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".partial")
    partial.unlink(missing_ok=True)
    try:
        with opener(entry["source"]["asset_url"], timeout=60) as response, partial.open("wb") as output:
            for block in iter(lambda: response.read(1024 * 1024), b""):
                output.write(block)
        actual_hash = sha256_file(partial)
        if partial.stat().st_size != expected_bytes or actual_hash != expected_hash:
            raise RuntimeError(f"downloaded model asset failed checksum: {entry['id']}")
        os.replace(partial, destination)
    finally:
        partial.unlink(missing_ok=True)
    return {"id": entry["id"], "path": entry["file"], "state": "downloaded_and_verified"}


def fetch_assets(root: Path, manifest: Path, model_ids: list[str]) -> list[dict[str, Any]]:
    document = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    entries = {entry["id"]: entry for entry in document["models"]}
    missing = sorted(set(model_ids) - entries.keys())
    if missing:
        raise KeyError(f"model IDs absent from manifest: {missing}")
    return [ensure_asset(root, entries[model_id]) for model_id in model_ids]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "models" / "manifest.yaml")
    parser.add_argument("--model-id", action="append", default=[])
    args = parser.parse_args()
    model_ids = args.model_id or ["B-M01-BASE"]
    result = fetch_assets(ROOT, args.manifest, model_ids)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
