# Baseline Video Source Readiness

Status: **video consumer ready; robot stream contract pending**.

The OpenCV frame-source boundary now accepts an integer camera index, local
file, or URL endpoint and emits fresh `FramePacket` objects. Reads are bounded
to one capture call. A failed read releases the capture, marks the source
disconnected, returns no frame, and never repeats the last image. Reconnection
is an explicit caller action with observable counters.

## Offline Replay Evidence

A local MP4 containing 20 frames derived from assignment smoke images was
generated and consumed through actual OpenCV:

- 20/20 frames read with sequential IDs and monotonic capture timestamps;
- every frame was BGR `240 x 320 x 3`;
- EOF produced `disconnected`, one recorded read failure, and no stale reuse;
- no robot endpoint or motor/control interface was involved.

This evidence validates file replay and the consumer lifecycle only. It is
explicitly not a real robot frame or stream-contract result, so Gate B0 remains
open on those two items.

Both Python environments pass all 55 tests. The future robot endpoint,
protocol, orientation, stable resolution, and stable FPS remain blank/unknown
until the user or Robotics team supplies them.
