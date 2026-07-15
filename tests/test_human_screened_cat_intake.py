from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image

from scripts.data.process_human_screened_cat_intake import (
    REPORTABLE_LABELS,
    process_intake,
)


FOLDER_NAMES = {
    "ragdoll": "ragdoll_photos",
    "singapura": "Singapura cats",
    "persian": "Persian",
    "sphynx": "Sphynx - Hairless Cat",
    "pallas": "Pallas-cat",
}


def write_image(path: Path, color: tuple[int, int, int], size=(200, 180)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, format="PNG")


def write_config(path: Path, input_root: Path, output_root: Path) -> None:
    path.write_text(
        f'''schema_version = 1

[paths]
input_root = "{input_root.as_posix()}"
output_root = "{output_root.as_posix()}"

[technical]
minimum_width = 160
minimum_height = 160
near_duplicate_hamming_distance = 4
allowed_extensions = [".jpg", ".jpeg", ".png"]
materialization = "copy"

[targets]
release_floor_total = 5
release_floor_per_class = 1
preferred_per_class = 2
not_target_floor = 1

[folder_prefixes]
pallas = "Pallas"
persian = "Persian"
ragdoll = "ragdoll"
singapura = "Singapura"
sphynx = "Sphynx"

[screening]
status = "human_screened_claimed"
reviewer_identity_recorded = false
note = "fixture"
''',
        encoding="utf-8",
    )


def fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    input_root = tmp_path / "input"
    for index, label in enumerate(REPORTABLE_LABELS):
        write_image(
            input_root / FOLDER_NAMES[label] / f"{label}_001.png",
            (20 + index * 30, 40 + index * 20, 60 + index * 10),
        )
    output_root = tmp_path / "output"
    config = tmp_path / "config.toml"
    write_config(config, input_root, output_root)
    return input_root, output_root, config


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_processes_canonical_classes_without_mutating_input(tmp_path: Path) -> None:
    input_root, output_root, config = fixture(tmp_path)
    before = {path: path.read_bytes() for path in input_root.rglob("*.png")}
    audit = process_intake(
        config_path=config,
        input_root=input_root,
        output_root=output_root,
    )
    assert audit["candidate_total"] == 5
    assert audit["release_floor_target_only_ready"] is True
    assert audit["gate_b1_ready"] is False
    assert audit["not_target_count"] == 0
    assert all(value == 1 for value in audit["candidate_counts"].values())
    assert before == {path: path.read_bytes() for path in input_root.rglob("*.png")}
    assert len(list((output_root / "clean_candidates").rglob("*.png"))) == 5


def test_rejects_low_resolution_and_redundant_exact_copy(tmp_path: Path) -> None:
    input_root, output_root, config = fixture(tmp_path)
    ragdoll = input_root / FOLDER_NAMES["ragdoll"]
    duplicate = ragdoll / "ragdoll_002.png"
    duplicate.write_bytes((ragdoll / "ragdoll_001.png").read_bytes())
    write_image(ragdoll / "ragdoll_003.png", (1, 2, 3), size=(120, 200))
    audit = process_intake(
        config_path=config,
        input_root=input_root,
        output_root=output_root,
    )
    assert audit["exact_duplicate_group_count"] == 1
    assert audit["exact_redundant_counts"] == {"ragdoll": 1}
    assert audit["below_minimum_counts"] == {"ragdoll": 1}
    manifest = read_manifest(output_root / "intake_manifest.csv")
    statuses = {row["technical_status"] for row in manifest if row["label"] == "ragdoll"}
    assert statuses == {
        "candidate",
        "rejected_below_minimum",
        "rejected_redundant_exact",
    }


def test_cross_label_exact_duplicate_is_fail_closed(tmp_path: Path) -> None:
    input_root, output_root, config = fixture(tmp_path)
    ragdoll = input_root / FOLDER_NAMES["ragdoll"] / "ragdoll_001.png"
    pallas = input_root / FOLDER_NAMES["pallas"] / "pallas_001.png"
    pallas.write_bytes(ragdoll.read_bytes())
    audit = process_intake(
        config_path=config,
        input_root=input_root,
        output_root=output_root,
    )
    assert audit["cross_label_exact_group_count"] == 1
    assert audit["candidate_total"] == 3
    assert "cross_label_exact_duplicates" in audit["blockers"]


def test_outputs_are_deterministic_without_materialization(tmp_path: Path) -> None:
    input_root, output_root, config = fixture(tmp_path)
    second = tmp_path / "output-second"
    first_audit = process_intake(
        config_path=config,
        input_root=input_root,
        output_root=output_root,
        materialize=False,
    )
    second_audit = process_intake(
        config_path=config,
        input_root=input_root,
        output_root=second,
        materialize=False,
    )
    assert first_audit == second_audit
    assert (output_root / "intake_manifest.csv").read_bytes() == (
        second / "intake_manifest.csv"
    ).read_bytes()
    assert json.loads((output_root / "audit.json").read_text(encoding="utf-8")) == first_audit
