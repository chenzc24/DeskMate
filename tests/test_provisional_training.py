from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from scripts.train_provisional_baseline import parse_results_csv


def write_results(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["epoch", "metrics/accuracy_top1", "metrics/accuracy_top5", "val/loss"],
        )
        writer.writeheader()
        writer.writerows(
            [
                {"epoch": "0", "metrics/accuracy_top1": "0.5", "metrics/accuracy_top5": "0.9", "val/loss": "1.2"},
                {"epoch": "1", "metrics/accuracy_top1": "0.7", "metrics/accuracy_top5": "0.95", "val/loss": "0.8"},
                {"epoch": "2", "metrics/accuracy_top1": "0.6", "metrics/accuracy_top5": "0.94", "val/loss": "0.9"},
            ]
        )


def test_parse_results_selects_best_top1_epoch(tmp_path: Path) -> None:
    path = tmp_path / "results.csv"
    write_results(path)
    result = parse_results_csv(path)
    assert result["epochs_completed"] == 3
    assert result["best_epoch_zero_based"] == 1
    assert result["best_val_top1"] == 0.7
    assert result["best_val_top5"] == 0.95


def test_parse_results_refuses_missing_accuracy(tmp_path: Path) -> None:
    path = tmp_path / "results.csv"
    path.write_text("epoch,val/loss\n0,1.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="top-1"):
        parse_results_csv(path)


def test_provisional_report_contract_fixture(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    manifest.write_text("sample_id,label\none,ragdoll\n", encoding="utf-8")
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    report = {
        "provisional_training_data_ready": True,
        "official_gate_b1_ready": False,
        "risk_scope": "development_only_not_final_release",
        "manifest_sha256": digest,
    }
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["manifest_sha256"] == digest
    assert loaded["official_gate_b1_ready"] is False
