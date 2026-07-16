# Robot online inference

`scripts/runtime/run_robot_pipeline.py` is the inference-only connection between
the Raspberry Pi camera stream and the frozen BD05 + M9 models. It never calls a
motor or serial-control endpoint.

On the GPU computer, start it with the Raspberry Pi's shared high-resolution
JPEG endpoint:

```powershell
cd C:\Users\32126\Desktop\Robitics\deskmate
.\.venv\Scripts\python.exe scripts\runtime\run_robot_pipeline.py --source http://<PI-IP>:5000/highres_feed --result-file runtime\latest_result.json --display
```

Each processed image is emitted as one JSON line and atomically replaces
`runtime/latest_result.json`. The `instant` result is for one image. The
`temporal_vote.result` appears after five consecutive valid frames and should be
used by any future UI or callback consumer.

The Raspberry Pi keeps exactly two camera outputs: `/video_feed` for the
low-latency operator preview, and `/highres_feed` for high-resolution JPEG.
The web preview and this AI process may both subscribe to `/highres_feed`, but
they share one cached high-resolution capture and encoder; subscribing does not
create a third camera stream. Do not point the AI process at `/video_feed` when
the high-resolution channel is available.

Add `--display` to open a live assisted view. Green boxes are BD05 detector
boxes; blue is the padded detector ROI passed to M9; yellow means there was no
detector box and M9 is classifying the centre fallback. The display overlays the
breed and confidence; press `Q` in that video window to stop it.

For a bounded connectivity test, add `--max-frames 10`. The same command accepts
a local video path or camera index, for example `--source 0`.

The model path is fixed by `models/frozen/baseline-bd05-m09.toml`: BD05 detects a
cat, the accepted box is padded by 25 percent, and a missing/rejected box uses an
80 percent centre fallback before M9 classifies one of ragdoll, singapura,
persian, sphynx, or pallas.
