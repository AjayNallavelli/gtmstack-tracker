#!/usr/bin/env python3
"""One-off: generate static/og.png (1200x630 social card) and static/logo.png (512x512) with Pillow.
Not run in CI (the PNGs are committed). Re-run after changing the copy:  pip install pillow && python scripts/make_og.py"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BRAND, DARK, WHITE = (37, 99, 235), (29, 78, 216), (255, 255, 255)
FONTS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]


def font(size, bold=True):
    try:
        return ImageFont.truetype(FONTS[0 if bold else 1], size)
    except OSError:
        return ImageFont.load_default(size)


def gradient(w, h):
    img = Image.new("RGB", (w, h), BRAND)
    px = img.load()
    for x in range(w):
        for y in range(h):
            f = (x / w + y / h) / 2
            px[x, y] = tuple(round(BRAND[i] + (DARK[i] - BRAND[i]) * f) for i in range(3))
    return img


def og():
    tools = json.loads((ROOT / "data" / "tools.json").read_text())["tools"]
    img = gradient(1200, 630)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((70, 70, 140, 140), 16, fill=WHITE)
    d.text((105, 105), "◆", font=font(44), fill=BRAND, anchor="mm")
    d.text((165, 105), "GTMStack Tracker", font=font(46), fill=WHITE, anchor="lm")
    y = 215
    for line in ["What AI sales tools", "actually cost, and", "when that changes."]:
        d.text((70, y), line, font=font(70), fill=WHITE)
        y += 86
    d.text((70, 500), f"Pricing for {len(tools)} AI SDR, cold email, data & deliverability tools",
           font=font(30, False), fill=(219, 234, 254))
    d.text((70, 545), "Re-checked daily · real price changes logged · free weekly email", font=font(30, False), fill=(219, 234, 254))
    img.save(ROOT / "static" / "og.png", optimize=True)


def logo():
    img = Image.new("RGB", (512, 512), BRAND)
    d = ImageDraw.Draw(img)
    d.text((256, 250), "◆", font=font(300), fill=WHITE, anchor="mm")
    img.save(ROOT / "static" / "logo.png", optimize=True)


if __name__ == "__main__":
    og()
    logo()
    print("wrote static/og.png and static/logo.png")
