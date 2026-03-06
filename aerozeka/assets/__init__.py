# -*- coding: utf-8 -*-
"""Resim varlıkları; eksikse placeholder üretilir (PIL varsa)."""

import os

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
PLACEHOLDER_KEYS = ("boeing737", "airbusa320")


def ensure_placeholders() -> None:
    """boeing737.png / airbusa320.png yoksa PIL ile oluşturur; PIL yoksa atlanır."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return
    for key in PLACEHOLDER_KEYS:
        path = os.path.join(ASSETS_DIR, f"{key}.png")
        if os.path.isfile(path):
            continue
        try:
            img = Image.new("RGB", (64, 64), color=(240, 248, 255))
            d = ImageDraw.Draw(img)
            text = "B737" if "boeing" in key else "A320"
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
            except Exception:
                font = ImageFont.load_default()
            bbox = d.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            d.text(((64 - tw) // 2, (64 - th) // 2), text, fill=(70, 70, 70), font=font)
            img.save(path)
        except Exception:
            pass
