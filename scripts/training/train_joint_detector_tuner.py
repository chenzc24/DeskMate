"""Fine-tune the baseline cat detector on the joint Sphynx/Pallas dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, default=Path("models/yolo26s.pt"))
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/downloads/detector_tuner_sphynx_pallas_yolo_20260715/data.yaml"),
    )
    parser.add_argument("--project", type=Path, default=Path("runs/detector_tuner"))
    parser.add_argument("--name", default="bd02-sphynx-pallas-seed-20260715")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="0")
    parser.add_argument("--seed", type=int, default=20260715)
    parser.add_argument("--resume", type=Path, help="Resume an interrupted Ultralytics run from last.pt")
    args = parser.parse_args()

    if args.resume:
        YOLO(str(args.resume.resolve())).train(resume=True, workers=0, device=args.device)
        return

    model = YOLO(str(args.model.resolve()))
    model.train(
        data=str(args.data.resolve()),
        epochs=args.epochs,
        patience=args.patience,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=0,
        project=str(args.project.resolve()),
        name=args.name,
        exist_ok=False,
        seed=args.seed,
        deterministic=True,
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        weight_decay=0.0005,
        warmup_epochs=3,
        freeze=10,
        close_mosaic=10,
        amp=True,
        cache=False,
        plots=True,
        save=True,
        verbose=True,
    )


if __name__ == "__main__":
    main()
