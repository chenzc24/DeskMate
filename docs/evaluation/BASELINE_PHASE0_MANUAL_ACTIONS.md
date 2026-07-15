# Baseline Phase 0 Manual-Action Dashboard

> Current state: **Gate B0 NOT PASSED**
>
> Machine evidence: `BASELINE_PHASE0_B0_REPORT.json`

The software and source-pilot checks are complete. Exactly two human-supplied
robot inputs still block Gate B0; both are intentionally fail-closed.

| Gate B0 action | State | Human owner | Evidence needed |
| --- | --- | --- | --- |
| B0-1: obtain one consented frame from the actual robot camera | OPEN | unassigned | saved frame plus a `recorded_robot` or `live_robot` skeleton report |
| B0-2: confirm the robot video-stream contract | OPEN | Robotics / unassigned | completed non-secret contract fields in `configs/baseline_phase0.toml` |

## B0-1: Actual Robot-Camera Frame

1. Confirm that recording the test scene is permitted and contains no private
   or unnecessary personal data.
2. Save one unmodified frame locally, for example at the ignored path
   `data/raw/robot/b0/frame-001.png`. Do not commit it.
3. Visually verify dimensions, rotation, mirroring, and color rendering.
4. From the repository root, run:

   ```powershell
   python scripts/run_phase0_skeleton.py `
     data/raw/robot/b0/frame-001.png `
     --source-kind recorded_robot `
     --output data/downloads/phase0_pilot/robot_frame_smoke.json
   ```

5. Confirm that the generated input evidence says
   `real_robot_evidence=true`. Then regenerate the B0 audit after B0-2 is also
   complete.

## B0-2: Robot Video-Stream Contract

Record the following with the Robotics owner. Do not place credentials, signed
URLs, tokens, or other secrets in Git.

| Contract field | Human-supplied value |
| --- | --- |
| Responsible owner and contact | |
| Protocol or capture type (USB, RTSP, HTTP/MJPEG, file, other) | |
| Endpoint configuration method; no secret value | |
| Stable resolution and expected FPS | |
| Pixel/color format (BGR, RGB, YUV, other) | |
| Rotation and mirroring | |
| Disconnect, timeout, and restart behavior | |
| Required room network or device setup | |
| Demo window/layout constraints | |
| Recording permission and retention rule | |

After confirmation, update the non-secret fields in
`configs/baseline_phase0.toml`. If the endpoint contains credentials or a
short-lived signed URL, record only its configuration method or environment
variable name in the repository.

## Separate Gate B1 Human Image Review

Image acceptance is visible here because it is the largest pending human task,
but it is **not a third Gate B0 failure**. It blocks the later dataset-freeze
Gate B1:

- the 130-image Phase 0 pilot remains quarantined; its Codex visual precheck
  has `acceptance_authority=false`;
- the full Phase 1 queue supersedes that pilot for dataset assembly and has
  **2,321 pending candidates and zero human-accepted images**;
- Singapura, Pallas, and Persian require two distinct agreeing reviewers;
- the ignored review queue is
  `data/downloads/phase1_candidates/review_batches/review_queue.csv`;
- 119 contact sheets are grouped below
  `data/downloads/phase1_candidates/review_batches/<label>/`.

After reviewers record their decisions, run:

```powershell
python scripts/audit_phase1_reviews.py
```

Exit code 3 is expected while required reviews are missing or disagree. Do not
freeze the split or begin official training while
`ready_to_freeze_split=false`.

## Definition Of B0 Cleared

Gate B0 is cleared only after both robot inputs above are supplied and
`python scripts/verify_gate_b0.py` exits 0 with status `PASS` and an empty
`failed_checks` list. Gate B1 image acceptance remains a separate subsequent
gate.
