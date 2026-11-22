#!/usr/bin/env python3
"""Render every bundled Material Symbol and verify that its SVG is not clipped."""

from __future__ import annotations

import io
import json
from pathlib import Path

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ICON_FILE = ROOT / "assets" / "icons" / "material_symbols_outlined.json"
RENDER_SIZE = 192


def main() -> None:
    icons = json.loads(ICON_FILE.read_text(encoding="utf-8"))
    failures: list[str] = []

    for name, svg in icons.items():
        try:
            png = cairosvg.svg2png(
                bytestring=svg.encode("utf-8"),
                output_width=RENDER_SIZE,
                output_height=RENDER_SIZE,
            )
            image = Image.open(io.BytesIO(png)).convert("RGBA")
            alpha = image.getchannel("A")
            bbox = alpha.getbbox()

            if image.size != (RENDER_SIZE, RENDER_SIZE):
                raise ValueError(f"unexpected dimensions: {image.size}")
            if bbox is None:
                raise ValueError("rendered image is fully transparent")

            left, top, right, bottom = bbox
            if left <= 0 or top <= 0 or right >= RENDER_SIZE or bottom >= RENDER_SIZE:
                raise ValueError(f"glyph touches canvas edge; possible clipping: {bbox}")
            if right - left < 12 or bottom - top < 12:
                raise ValueError(f"glyph is suspiciously small: {bbox}")

        except Exception as exc:
            failures.append(f"{name}: {exc}")

    if failures:
        raise SystemExit("Material Symbols validation failed:\n" + "\n".join(failures))

    print(f"Validated {len(icons)} Material Symbols: transparent canvas, non-empty glyphs, no edge clipping.")


if __name__ == "__main__":
    main()
