"""Build local contact sheets for human review of quarantine pilot images."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


def find_image(root: Path, source_kind: str, label: str, image_id: str) -> Path:
    source_dirs = {
        "wikimedia_commons": "commons",
        "inaturalist": "inaturalist",
        "oxford_iiit_pet": "oxford_iiit_pet",
        "gbif": "gbif",
    }
    source_dir = source_dirs[source_kind]
    matches = sorted((root / source_dir / label).rglob(f"{image_id}.*"))
    if not matches:
        raise FileNotFoundError(f"no local image for {image_id}")
    return matches[0]


def build_sheet(
    entries: list[tuple[Path, str]],
    *,
    title: str,
    output: Path,
    columns: int = 4,
) -> None:
    thumb_width, thumb_height, caption_height = 240, 180, 44
    rows = (len(entries) + columns - 1) // columns
    sheet = Image.new(
        "RGB", (columns * thumb_width, 52 + rows * (thumb_height + caption_height)), "white"
    )
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 14), title, fill="black")
    for index, (path, caption) in enumerate(entries):
        column = index % columns
        row = index // columns
        x = column * thumb_width
        y = 52 + row * (thumb_height + caption_height)
        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.thumbnail((thumb_width - 10, thumb_height - 10))
            offset_x = x + (thumb_width - image.width) // 2
            offset_y = y + (thumb_height - image.height) // 2
            sheet.paste(image, (offset_x, offset_y))
        draw.rectangle((x, y, x + thumb_width - 1, y + thumb_height - 1), outline="#777777")
        draw.text((x + 5, y + thumb_height + 4), caption[:34], fill="black")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, format="PNG", optimize=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--pilot-root", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    pilot_root = args.pilot_root or args.manifest.parent
    output_dir = args.output_dir or pilot_root / "contact_sheets"

    groups: dict[tuple[str, str, str], list[tuple[Path, str]]] = defaultdict(list)
    missing: list[str] = []
    with args.manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            try:
                image_path = find_image(
                    pilot_root, row["source_kind"], row["label"], row["image_id"]
                )
            except FileNotFoundError:
                missing.append(row["image_id"])
                continue
            caption = f"{row['image_id']} | {row['license_name']}"
            groups[(row["source_kind"], row["label"], row["source_dataset"])].append((image_path, caption))

    outputs: list[str] = []
    for (source_kind, label, dataset), entries in sorted(groups.items()):
        slug = re.sub(r"[^a-z0-9]+", "_", dataset.casefold()).strip("_")
        output = output_dir / f"{source_kind}_{label}_{slug}.png"
        build_sheet(
            entries,
            title=f"{source_kind} / {label} / {dataset} / quarantine",
            output=output,
        )
        outputs.append(str(output))
    report = {"outputs": outputs, "missing": missing, "ok": not missing}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
