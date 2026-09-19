#!/usr/bin/env python3
"""Discover local images, report dimensions, and preprocess with Pillow when available."""

from __future__ import annotations

import argparse
import json
import struct
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tif", ".tiff"}


def discover(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in SUFFIXES)


def dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()[:32]
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    if data.startswith((b"GIF87a", b"GIF89a")) and len(data) >= 10:
        return struct.unpack("<HH", data[6:10])
    if data.startswith(b"BM") and len(data) >= 26:
        return struct.unpack("<II", data[18:26])
    try:
        from PIL import Image
        with Image.open(path) as image:
            return image.size
    except (ImportError, OSError):
        return None


def preprocess(path: Path, output: Path, crop: list[int] | None, scale: int, contrast: float) -> dict:
    try:
        from PIL import Image, ImageEnhance
    except ImportError as error:
        raise ValueError("Pillow is unavailable; inspect the original with available local viewer") from error
    with Image.open(path) as image:
        full_size = image.size
        if crop:
            if len(crop) != 4:
                raise ValueError("crop must contain left,top,right,bottom")
            image = image.crop(tuple(crop))
        if scale != 1:
            if not 1 <= scale <= 8:
                raise ValueError("scale must be between 1 and 8")
            image = image.resize((image.width * scale, image.height * scale))
        if contrast != 1:
            image = ImageEnhance.Contrast(image).enhance(contrast)
        output.parent.mkdir(parents=True, exist_ok=True)
        image.save(output)
        return {"source_size": full_size, "output_size": image.size, "output": str(output)}


class SelfTests(unittest.TestCase):
    def test_discovery_and_png_dimensions(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)
            png = root / "test.png"
            png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8 + struct.pack(">II", 7, 9) + b"\x00" * 8)
            self.assertEqual(discover(root), [png])
            self.assertEqual(dimensions(png), (7, 9))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="command")
    find = sub.add_parser("discover")
    find.add_argument("--root", type=Path, default=Path("/app"))
    inspect = sub.add_parser("inspect")
    inspect.add_argument("--image", required=True, type=Path)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--image", required=True, type=Path)
    prepare.add_argument("--output", required=True, type=Path)
    prepare.add_argument("--crop", help="left,top,right,bottom")
    prepare.add_argument("--scale", type=int, default=1)
    prepare.add_argument("--contrast", type=float, default=1)
    args = parser.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SelfTests)).wasSuccessful() else 1
    if args.command == "discover":
        print(json.dumps([{"path": str(path), "dimensions": dimensions(path)} for path in discover(args.root)], indent=2))
    elif args.command == "inspect":
        print(json.dumps({"path": str(args.image), "dimensions": dimensions(args.image)}, indent=2))
    elif args.command == "prepare":
        crop = [int(value) for value in args.crop.split(",")] if args.crop else None
        print(json.dumps(preprocess(args.image, args.output, crop, args.scale, args.contrast), indent=2))
    else:
        parser.error("choose discover, inspect, or prepare")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
