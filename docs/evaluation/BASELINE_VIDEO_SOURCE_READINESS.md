# Baseline Video Source Readiness

Status: **video consumer ready; robot JPG delivery contract pending**.

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

Both Python environments pass all 61 currently discovered tests. The provisional requested profile
is 480 x 480 JPEG quality 85 at 8 FPS, upright and not mirrored, decoded by
OpenCV to BGR. These are requested values rather than real-stream evidence.
The delivery protocol, endpoint, observed resolution/FPS, source-frame identity,
and disconnect behavior remain unverified until Robotics supplies a real JPG
and delivery details.
