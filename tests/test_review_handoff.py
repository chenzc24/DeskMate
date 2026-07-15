from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_phase1_review_handoff import build_handoff  # noqa: E402


FIELDS = [
    "image_id",
    "label",
    "source_kind",
    "source_dataset",
    "source_group_id",
    "duplicate_cluster_id",
    "batch",
    "decision",
    "reviewer",
    "second_decision",
    "second_reviewer",
    "notes",
]


def write_queue(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def row(image_id: str = "commons-1", batch: str = "ragdoll-001") -> dict[str, str]:
    value = {field: "" for field in FIELDS}
    value.update(
        {
            "image_id": image_id,
            "label": "ragdoll",
            "source_kind": "wikimedia_commons",
            "source_dataset": "test",
            "source_group_id": image_id,
            "batch": batch,
        }
    )
    return value


def fixture_paths(tmp_path: Path, rows: list[dict[str, str]]):
    source = tmp_path / "source"
    queue = tmp_path / "queue.csv"
    readme = tmp_path / "README.md"
    output = tmp_path / "handoff"
    (source / "commons" / "ragdoll").mkdir(parents=True)
    readme.write_text("review instructions\n", encoding="utf-8")
    write_queue(queue, rows)
    return source, queue, readme, output


def test_builds_minimal_handoff_with_inventory(tmp_path: Path) -> None:
    rows = [row()]
    source, queue, readme, output = fixture_paths(tmp_path, rows)
    (source / "commons" / "ragdoll" / "commons-1.jpg").write_bytes(b"jpeg")

    summary = build_handoff(
        source_root=source,
        queue_path=queue,
        readme_path=readme,
        output_dir=output,
    )

    assert summary["image_count"] == 1
    assert summary["contact_sheets_included"] is False
    assert (output / "images" / "ragdoll" / "commons-1.jpg").read_bytes() == b"jpeg"
    assert not any(path.is_dir() for path in (output / "images" / "ragdoll").iterdir())
    assert (output / "README.md").read_text(encoding="utf-8") == "review instructions\n"
    with (output / "inventory.csv").open(encoding="utf-8", newline="") as handle:
        inventory = list(csv.DictReader(handle))
    assert inventory[0]["image_id"] == "commons-1"
    assert len(inventory[0]["sha256"]) == 64


@pytest.mark.parametrize(
    "rows, expected",
    [
        ([row(), row()], "duplicate image_id"),
        ([row(image_id="../escape")], "unsafe or empty image_id"),
        ([row(batch="pallas-001")], "unsafe or mismatched batch"),
    ],
)
def test_refuses_unsafe_or_ambiguous_queue_rows(
    tmp_path: Path, rows: list[dict[str, str]], expected: str
) -> None:
    source, queue, readme, output = fixture_paths(tmp_path, rows)
    with pytest.raises(ValueError, match=expected):
        build_handoff(
            source_root=source,
            queue_path=queue,
            readme_path=readme,
            output_dir=output,
        )


def test_refuses_missing_image_and_existing_output(tmp_path: Path) -> None:
    rows = [row()]
    source, queue, readme, output = fixture_paths(tmp_path, rows)
    with pytest.raises(FileNotFoundError, match="expected at least one image"):
        build_handoff(
            source_root=source,
            queue_path=queue,
            readme_path=readme,
            output_dir=output,
        )


def test_deduplicates_identical_source_aliases_but_refuses_conflicts(
    tmp_path: Path,
) -> None:
    rows = [row()]
    source, queue, readme, output = fixture_paths(tmp_path, rows)
    first = source / "commons" / "ragdoll" / "commons-1.jpg"
    alias = source / "commons" / "ragdoll" / "alias" / "commons-1.jpg"
    first.write_bytes(b"same")
    alias.parent.mkdir()
    alias.write_bytes(b"same")
    summary = build_handoff(
        source_root=source,
        queue_path=queue,
        readme_path=readme,
        output_dir=output,
    )
    assert summary["image_count"] == 1

    other_output = tmp_path / "other-handoff"
    alias.write_bytes(b"different")
    with pytest.raises(ValueError, match="different file contents"):
        build_handoff(
            source_root=source,
            queue_path=queue,
            readme_path=readme,
            output_dir=other_output,
        )

    output.mkdir(exist_ok=True)
    with pytest.raises(FileExistsError, match="output already exists"):
        build_handoff(
            source_root=source,
            queue_path=queue,
            readme_path=readme,
            output_dir=output,
        )
