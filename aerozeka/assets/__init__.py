# -*- coding: utf-8 -*-
"""Resim varlıkları; eksikse placeholder üretilir (PIL varsa)."""

import os

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
PLACEHOLDER_KEYS = ("boeing737", "airbusa320")
# Uçak resmi yoksa kullanılacak genel gri placeholder
PLACEHOLDER_PLANE = "placeholder_plane"


def ensure_placeholders() -> None:
    """Eksik resimleri PIL ile oluşturur: boeing737, airbusa320, placeholder_plane."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return
    for key in list(PLACEHOLDER_KEYS) + [PLACEHOLDER_PLANE]:
        path = os.path.join(ASSETS_DIR, f"{key}.png")
        if os.path.isfile(path):
            continue
        try:
            img = Image.new("RGB", (64, 64), color=(200, 200, 200) if key == PLACEHOLDER_PLANE else (240, 248, 255))
            d = ImageDraw.Draw(img)
            if key == PLACEHOLDER_PLANE:
                text = "Uçak"
            else:
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
