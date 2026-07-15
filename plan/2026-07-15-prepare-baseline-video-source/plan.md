# Prepare Baseline Video Source And Offline Replay

## Outcome

Implement the real OpenCV frame-consumer boundary and deterministic offline
replay smoke so a future USB index, RTSP URL, or HTTP/MJPEG endpoint can be
inserted without changing inference/runtime contracts. Do not claim local
fixture replay as robot-stream evidence.

## Owned Files And Directories

- new video-source module under `src/deskmate_baseline/`
- new replay/smoke scripts under `scripts/`
- targeted tests under `tests/`
- `docs/evaluation/BASELINE_VIDEO_SOURCE_READINESS.md`
- `docs/evaluation/BASELINE_VIDEO_SOURCE_READINESS.json`
- `plan/log.md`
- this target plan
- ignored generated replay videos and smoke output

## Read-Only And Deferred Paths

- all requirement, high-level plan, data/review, model/training/evaluation files
- `configs/baseline_phase0.toml` blank robot endpoint/protocol/orientation fields
- all robot hardware, credentials, network endpoints, and commands
- parent workspace

## Contracts

- Support integer camera index, local file, and URL endpoints through one
  `FrameSource` implementation with dependency injection for deterministic tests.
- Each successful read returns a new `FramePacket` with current timestamp,
  dimensions, source identity, and BGR pixels.
- Failed read immediately invalidates readiness, releases the capture, returns
  no frame, and increments observable failure/reconnect state. It never repeats
  the last frame.
- Reconnect is explicit and bounded per call. No hidden infinite retry loop or
  blocking sleep exists inside capture/read.
- Orientation and color conversion remain deferred until the robot contract is
  known. OpenCV native BGR is the current boundary.
- Local fixture replay is `offline_fixture` evidence only and cannot pass B0.

## Validation

- fake-capture tests for open/read/failure/release/reconnect/close
- local generated MP4 replay through actual OpenCV in `.venv`
- verify increasing frame IDs, fresh timestamps, BGR shape, EOF invalidation,
  no stale-frame reuse, and no motor/control dependency
- run all tests in default and pinned environments
- confirm Gate B0 still fails the same robot checks and Gate B1 remains pending
- verify requirement immutability and diff/status checks

## Robot Motion

None. No robot endpoint is opened.

## Commit Intent

No branch, commit, push, or PR unless explicitly requested.

## Validation Results

Completed the bounded video-consumer and offline replay preparation without
opening a robot endpoint.

- Added one OpenCV source for camera index, local file, or URL endpoints with
  injected capture support for deterministic tests.
- Successful reads produce fresh BGR `FramePacket` values and increasing frame
  IDs. Failure releases capture, records disconnect, returns no frame, and does
  not reuse the last packet.
- Reconnect is explicit and counted; no hidden retry loop or sleep exists.
- Actual OpenCV generated and consumed a 20-frame, 320x240 local MP4. All frame
  IDs and timestamps were monotonic; EOF disconnected with no stale reuse.
- The replay is marked `offline_fixture_only` and `real_robot_evidence=false`.
- Both Python environments pass all 55 tests. JSON parsing, two checksums, B0/B1
  audits, requirement immutability, and `git diff --check` pass.

Robot endpoint/protocol/orientation/resolution/FPS remain blank or unknown.
No robot connection, motion, branch, commit, push, or PR was performed.
