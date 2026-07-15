from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from deskmate_baseline.contracts import INTERNAL_LABELS
from deskmate_baseline.localization import LocalizerBox, LocalizerObservation
from scripts.derive_detector_classifier_views import derive_views


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class FakeBackend:
    cat_class_id = 15

    def load(self) -> None:
        pass

    def warmup(self) -> None:
        pass

    def close(self) -> None:
        pass

    def infer(self, frame):
        if frame.frame_id == 4:
            return LocalizerObservation.invalid(
                frame=frame,
                model_id="B-D01",
                inferred_at_ns=frame.captured_at_ns,
                reason="fixture_invalid",
            )
        boxes = ()
        if frame.frame_id != 1:
            boxes = (
                LocalizerBox((0.2, 0.1, 0.8, 0.9), 0.9, 15),
            )
            if frame.frame_id == 2:
                boxes += (LocalizerBox((0.1, 0.2, 0.4, 0.7), 0.6, 15),)
        return LocalizerObservation(
            task="cat_localization",
            boxes=boxes,
            model_id="B-D01",
            frame_id=frame.frame_id,
            captured_at_ns=frame.captured_at_ns,
            inferred_at_ns=frame.captured_at_ns,
            valid=True,
        )


def fixture(tmp_path: Path, *, negative_dataset="Category:Maine Coon cats"):
    base_root = tmp_path / "base"
    manifest = base_root / "provisional_split_manifest.csv"
    rows = []
    for index, label in enumerate(INTERNAL_LABELS):
        relative = Path("yolo_classify") / "train" / f"{index}_{label}" / f"sample-{index}.jpg"
        path = base_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        image = np.zeros((100, 200, 3), dtype=np.uint8)
        image[10:90, 40:160] = (20 + index * 20, 80, 160)
        assert cv2.imwrite(str(path), image)
        rows.append(
            {
                "sample_id": f"sample-{index}",
                "label": label,
                "split": "train",
                "source_image_id": f"source-{index}",
                "source_kind": "human_screened_intake" if label != "not_target" else "wikimedia_commons",
                "source_relative_path": relative.as_posix(),
                "materialized_relative_path": relative.as_posix(),
                "exact_sha256": sha(path),
            }
        )
    write_csv(
        manifest,
        ["sample_id", "label", "split", "source_image_id", "source_kind", "source_relative_path", "materialized_relative_path", "exact_sha256"],
        rows,
    )
    negative_manifest = tmp_path / "negative.csv"
    write_csv(
        negative_manifest,
        ["image_id", "label", "source_dataset"],
        [{"image_id": "source-5", "label": "not_target", "source_dataset": negative_dataset}],
    )
    detector = tmp_path / "detector.pt"
    detector.write_bytes(b"detector-fixture")
    output = tmp_path / "output"
    config = tmp_path / "config.toml"
    config.write_text(
        f'''schema_version = 1
freeze_id = "fixture"
generated_at = "2026-07-15T00:00:00+08:00"
[paths]
base_split_manifest = "{manifest.as_posix()}"
base_dataset_root = "{base_root.as_posix()}"
target_source_root = "{base_root.as_posix()}"
negative_source_root = "{base_root.as_posix()}"
negative_source_manifest = "{negative_manifest.as_posix()}"
output_root = "{output.as_posix()}"
[detector]
model_id = "B-D01"
checkpoint = "{detector.as_posix()}"
expected_sha256 = "{sha(detector)}"
task = "detect"
native_class = "cat"
imgsz = 640
device = 0
confidence_threshold = 0.25
minimum_box_area_ratio = 0.02
maximum_candidates = 5
maximum_frame_age_ms = 500.0
[views]
padding_ratio = 0.15
jpeg_quality = 95
minimum_crop_width = 32
minimum_crop_height = 32
strategy = "one_view_per_parent"
target_hit_view = "bd01_crop"
target_miss_view = "original"
known_other_breed_hit_view = "bd01_crop"
background_view = "original"
known_other_breed_source_dataset = "Category:Maine Coon cats"
[training]
folder_root = "one_view_yolo_classify"
sampling_unit = "parent_image_id"
selected_views_per_parent = 1
official_counts_use_base_images = true
''',
        encoding="utf-8",
    )
    return config, output


def read_views(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_one_view_per_parent_with_hit_miss_multi_and_invalid(tmp_path: Path) -> None:
    config, output = fixture(tmp_path)
    report = derive_views(config_path=config, backend=FakeBackend())
    assert report["parent_count"] == 6
    assert report["selected_view_count"] == 6
    assert report["view_count"] == 10
    assert report["coverage"]["singapura"] == {"miss": 1}
    assert report["coverage"]["persian"] == {"multi_box": 1}
    assert report["coverage"]["pallas"] == {"invalid": 1}
    views = read_views(output / "view_manifest.csv")
    selected = [row for row in views if row["selected_for_folder_training"] == "true"]
    assert len(selected) == len({row["parent_image_id"] for row in selected}) == 6
    assert len(list((output / "one_view_yolo_classify").rglob("*.jpg"))) == 6
    assert report["selected_kind_counts"]["not_target"] == {"bd01_crop": 1}


def test_background_negative_keeps_original_even_on_detector_hit(tmp_path: Path) -> None:
    config, output = fixture(tmp_path, negative_dataset="Category:Desks")
    report = derive_views(config_path=config, backend=FakeBackend())
    assert report["selected_kind_counts"]["not_target"] == {"original": 1}
    views = read_views(output / "view_manifest.csv")
    negative = [row for row in views if row["label"] == "not_target"]
    assert len(negative) == 1
    assert negative[0]["selection_reason"] == "background_original_policy"
