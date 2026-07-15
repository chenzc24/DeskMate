"""Read-only inventory for DeskMate data, runs, and model artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
MODEL_SUFFIXES = {".pt", ".pth", ".ckpt", ".onnx", ".engine", ".safetensors"}
SKIP_PARTS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}
MANIFEST_FILE = re.compile(
    r"^\s*(?:-\s*)?file:\s*['\"]?([^'\"#\r\n]+)", re.MULTILINE
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def files_under(path: Path) -> Iterable[Path]:
    if not path.exists():
        return ()
    return (
        item
        for item in path.rglob("*")
        if item.is_file() and not any(part in SKIP_PARTS for part in item.parts)
    )


def summarize(path: Path, project_root: Path) -> dict[str, Any]:
    files = list(files_under(path))
    return {
        "path": path.relative_to(project_root).as_posix(),
        "files": len(files),
        "bytes": sum(item.stat().st_size for item in files),
    }


def child_summaries(path: Path, project_root: Path) -> list[dict[str, Any]]:
    if not path.is_dir():
        return []
    return [
        summarize(child, project_root)
        for child in sorted(path.iterdir(), key=lambda item: item.name.casefold())
        if child.is_dir()
    ]


def registered_model_paths(project_root: Path) -> set[str]:
    manifest = project_root / "models" / "manifest.yaml"
    if not manifest.is_file():
        return set()
    text = manifest.read_text(encoding="utf-8")
    return {match.strip().replace("\\", "/") for match in MANIFEST_FILE.findall(text)}


def model_inventory(project_root: Path) -> tuple[list[dict[str, Any]], list[list[str]]]:
    registered = registered_model_paths(project_root)
    candidates: list[Path] = []
    for base in (project_root / "models", project_root / "runs"):
        candidates.extend(
            item for item in files_under(base) if item.suffix.casefold() in MODEL_SUFFIXES
        )
    candidates.extend(
        item
        for item in project_root.iterdir()
        if item.is_file() and item.suffix.casefold() in MODEL_SUFFIXES
    )

    records: list[dict[str, Any]] = []
    by_hash: dict[str, list[str]] = defaultdict(list)
    for path in sorted(set(candidates)):
        relative = path.relative_to(project_root).as_posix()
        digest = sha256(path)
        by_hash[digest].append(relative)
        records.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": digest,
                "registered": relative in registered,
                "root_level": path.parent == project_root,
            }
        )
    duplicates = [paths for paths in by_hash.values() if len(paths) > 1]
    return records, sorted(duplicates, key=lambda paths: paths[0])


def build_inventory(project_root: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    models, duplicate_models = model_inventory(project_root)
    return {
        "schema_version": 1,
        "project_root": str(project_root),
        "roots": [
            summarize(project_root / name, project_root)
            for name in ("data", "runs", "models", "artifacts")
            if (project_root / name).exists()
        ],
        "data_workspaces": child_summaries(
            project_root / "data" / "downloads", project_root
        ),
        "run_groups": child_summaries(project_root / "runs", project_root),
        "models": models,
        "duplicate_model_groups": duplicate_models,
        "warnings": [
            *("root_level_model_file" for item in models if item["root_level"]),
            *("unregistered_model_file" for item in models if not item["registered"]),
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_inventory(args.root)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = args.output if args.output.is_absolute() else args.root / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
