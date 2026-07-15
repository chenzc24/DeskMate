from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np

from deskmate_baseline.contracts import FramePacket
from deskmate_baseline.localization import (
    UltralyticsCatLocalizerBackend,
    route_classification_roi,
)


ROOT = Path(__file__).resolve().parents[1]
LABELS = ("ragdoll", "singapura", "persian", "sphynx", "pallas")
CLASS_DIRS = {label: f"{index}_{label}" for index, label in enumerate(LABELS)}
BURST_LABELS = {
    "burst_04": "sphynx",
    "burst_11": "sphynx",
    "burst_12": "persian",
    "burst_15": "ragdoll",
    "burst_16": "singapura",
    "burst_17": "singapura",
    "burst_22": "pallas",
    "burst_23": "ragdoll",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_image(path: Path) -> np.ndarray:
    image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"cannot decode image: {path}")
    return image


def burst_candidates(audit_rows: list[dict[str, str]]) -> dict[str, list[Path]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in audit_rows:
        grouped[row["burst_id"]].append(row)
    result: dict[str, list[Path]] = {}
    for burst_id in BURST_LABELS:
        samples = grouped[burst_id]
        first = ROOT / samples[0]["source_path"]
        last = ROOT / samples[-1]["source_path"]
        candidates = sorted(
            path
            for path in first.parent.glob("*.jpg")
            if first.name <= path.name <= last.name
        )
        expected = int(samples[0]["burst_frame_count"])
        if len(candidates) != expected:
            raise RuntimeError(
                f"{burst_id} expected {expected} frames, found {len(candidates)}"
            )
        result[burst_id] = candidates
    return result


def evenly_select(paths: list[Path], count: int) -> list[Path]:
    if len(paths) < count:
        raise ValueError(f"need {count} candidates, found {len(paths)}")
    indices = np.linspace(0, len(paths) - 1, count, dtype=int)
    if len(set(indices.tolist())) != count:
        raise RuntimeError("even selection produced duplicate indices")
    return [paths[int(index)] for index in indices]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/downloads/baseline_robot_adaptation_20260715",
    )
    parser.add_argument("--samples-per-class", type=int, default=70)
    parser.add_argument("--validation-per-class", type=int, default=10)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    audit = read_csv(
        ROOT
        / "data/downloads/Camera/model_test_selection_20260715_audit/audit_samples.csv"
    )
    diagnostic = read_csv(
        ROOT / "data/downloads/Camera/model_test_selection_20260715/manifest.csv"
    )
    excluded_sources = {(ROOT / row["source_relative_path"]).resolve() for row in diagnostic}
    candidates_by_burst = burst_candidates(audit)
    candidates_by_label: dict[str, list[Path]] = defaultdict(list)
    for burst_id, label in BURST_LABELS.items():
        candidates_by_label[label].extend(
            path
            for path in candidates_by_burst[burst_id]
            if path.resolve() not in excluded_sources
        )
    detector_path = ROOT / "models/yolo26s.pt"
    detector = UltralyticsCatLocalizerBackend(
        checkpoint=detector_path,
        device=0,
        imgsz=640,
        confidence_threshold=0.25,
        minimum_box_area_ratio=0.02,
        maximum_frame_age_ms=5000,
    )
    detector.load()
    detector.warmup()
    rows: list[dict[str, object]] = []
    frame_id = 0
    for label in LABELS:
        selected = evenly_select(
            sorted(candidates_by_label[label]), args.samples_per_class
        )
        validation_indices = set(
            np.linspace(
                0, len(selected) - 1, args.validation_per_class, dtype=int
            ).tolist()
        )
        for index, source in enumerate(selected):
            split = "val" if index in validation_indices else "train"
            image = read_image(source)
            height, width = image.shape[:2]
            frame = FramePacket(
                frame_id=frame_id,
                captured_at_ns=time.time_ns(),
                image_bgr=image,
                source=str(source),
                width=width,
                height=height,
            )
            observation = detector.infer(frame)
            routed = route_classification_roi(
                frame,
                observation,
                box_is_stable=bool(observation.valid and observation.boxes),
                padding_ratio=0.15,
                fallback_center_scale=0.8,
                minimum_padded_short_side_pixels=32,
            )
            filename = f"robot-{label}-{index + 1:03d}.jpg"
            destination = output / "yolo_classify" / split / CLASS_DIRS[label] / filename
            destination.parent.mkdir(parents=True, exist_ok=True)
            success, encoded = cv2.imencode(
                ".jpg", routed.image_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95]
            )
            if not success:
                raise RuntimeError(f"cannot encode routed ROI: {source}")
            encoded.tofile(str(destination))
            burst_id = next(
                burst
                for burst, paths in candidates_by_burst.items()
                if source in paths
            )
            rows.append(
                {
                    "sample_id": Path(filename).stem,
                    "label": label,
                    "split": split,
                    "burst_id": burst_id,
                    "source_relative_path": source.relative_to(ROOT).as_posix(),
                    "source_sha256": sha256_file(source),
                    "dataset_relative_path": destination.relative_to(
                        output / "yolo_classify"
                    ).as_posix(),
                    "view_sha256": sha256_file(destination),
                    "route_mode": routed.mode,
                    "route_reason": routed.route_reason,
                    "detector_box_count": len(observation.boxes),
                    "diagnostic_exact_source_excluded": True,
                }
            )
            frame_id += 1
    manifest = output / "robot_adaptation_manifest.csv"
    with manifest.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    counts = Counter((str(row["split"]), str(row["label"])) for row in rows)
    final_counts = {
        split: {label: counts[(split, label)] for label in LABELS}
        for split in ("train", "val")
    }
    report = {
        "schema_version": 1,
        "status": "ROBOT_DOMAIN_ADAPTATION_READY",
        "dataset_root": str(output / "yolo_classify"),
        "manifest": str(manifest),
        "manifest_sha256": sha256_file(manifest),
        "labels": list(LABELS),
        "not_target_present": False,
        "final_counts": final_counts,
        "total": len(rows),
        "source_burst_labels": BURST_LABELS,
        "diagnostic_exact_sources_excluded": len(excluded_sources),
        "same_burst_as_diagnostic": True,
        "route_counts": dict(Counter(str(row["route_mode"]) for row in rows)),
        "detector_sha256": sha256_file(detector_path),
    }
    (output / "robot_adaptation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
