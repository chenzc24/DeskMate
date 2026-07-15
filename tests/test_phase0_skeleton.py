from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_assignment_image_runs_only_as_smoke_fixture() -> None:
    image = (
        ROOT
        / "References"
        / "The requirement"
        / "SWS3009A_Assg_assets"
        / "cat-000.png"
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "runtime" / "run_phase0_skeleton.py"),
            str(image),
            "--source-kind",
            "assignment_smoke",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)
    assert report["placeholder_only"]
    assert not report["input"]["real_robot_evidence"]
    assert report["contracts"]["first_job_kind"] == "confirmation"
    assert report["contracts"]["second_job_kind"] == "preview"
    assert report["contracts"]["preview_console_line"] is None
    assert report["contracts"]["confirmation_line"].find("CONFIRMED species=ragdoll") > 0
    assert report["contracts"]["duplicate_confirmation_line"] is None
    assert report["contracts"]["fresh_observation_accepted"]
    assert report["contracts"]["temporal_size_after_stale"] == 0
    assert report["contracts"]["queue_sizes_after_pop"] == [0, 0]
    assert not report["contracts"]["motion_enabled"]
