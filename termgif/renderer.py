"""
Render a list of (svg_str, hold_ms) frames into a GIF using Playwright + Pillow.

Playwright is used to render each SVG in a headless Chromium browser, which handles
Textual's custom fonts and CSS correctly. Each rendered PNG is then assembled into
an animated GIF by Pillow.
"""

from __future__ import annotations
import io
import os
import tempfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright


_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body {{
    margin: 0; padding: 0;
    background: transparent;
    display: inline-block;
  }}
</style>
</head>
<body>{svg}</body>
</html>"""


def _svg_to_png(svg: str, page) -> bytes:
    with tempfile.NamedTemporaryFile(
        suffix=".html", delete=False, mode="w", encoding="utf-8"
    ) as f:
        f.write(_HTML_TEMPLATE.format(svg=svg))
        tmp = f.name

    try:
        url = "file:///" + tmp.replace("\\", "/")
        page.goto(url)
        page.wait_for_load_state("networkidle")

        svg_el = page.query_selector("svg")
        if svg_el:
            bb = svg_el.bounding_box()
            if bb:
                page.set_viewport_size({
                    "width": max(1, int(bb["width"]) + 4),
                    "height": max(1, int(bb["height"]) + 4),
                })

        return page.screenshot(full_page=True)
    finally:
        os.unlink(tmp)


def render(
    frames: list[tuple[str, int]],
    output_path: str | Path,
    gif_width: int = 900,
) -> Path:
    """
    Convert SVG frames to an animated GIF.

    Args:
        frames:      List of (svg_str, hold_ms) pairs.
        output_path: Where to write the .gif.
        gif_width:   Pixel width of the output GIF (height scales proportionally).

    Returns:
        Path to the written GIF.
    """
    output_path = Path(output_path)
    images: list[Image.Image] = []
    delays: list[int] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()

        for svg, hold_ms in frames:
            png_bytes = _svg_to_png(svg, page)
            img = Image.open(io.BytesIO(png_bytes))

            # Uniform width resize
            ratio = gif_width / img.width
            new_h = max(1, int(img.height * ratio))
            img = img.resize((gif_width, new_h), Image.LANCZOS).convert("RGB")

            images.append(img)
            delays.append(hold_ms)

        browser.close()

    if not images:
        raise ValueError("No frames to render.")

    # Quantise to palette mode for GIF
    palette_imgs = [
        img.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
        for img in images
    ]

    palette_imgs[0].save(
        output_path,
        save_all=True,
        append_images=palette_imgs[1:],
        loop=0,
        duration=delays,
        optimize=True,
    )

    return output_path
