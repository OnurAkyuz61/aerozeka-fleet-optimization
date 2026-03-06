# -*- coding: utf-8 -*-
"""Uçak listesi: thumbnail (PIL), kapasite, yakıt; en ideal yeşil vurgu + Neden Seçildi?."""

import os
import tkinter as tk
from tkinter import ttk
from typing import List, Optional

from aerozeka.core import AircraftCandidate

# Pillow opsiyonel; yoksa sadece metin gösterilir
try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

THUMB_W, THUMB_H = 48, 48


def _placeholder_image(key: str):
    """Resim yoksa placeholder: renkli kare + kısa metin."""
    if not _PIL_AVAILABLE:
        return None
    try:
        img = Image.new("RGB", (THUMB_W, THUMB_H), color=(220, 230, 240))
        d = ImageDraw.Draw(img)
        text = (key[:6].upper() if key else "?")
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 10)
        except Exception:
            font = ImageFont.load_default()
        bbox = d.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(((THUMB_W - tw) // 2, (THUMB_H - th) // 2), text, fill=(80, 80, 80), font=font)
        return img
    except Exception:
        return Image.new("RGB", (THUMB_W, THUMB_H), color=(200, 200, 200))


def _load_thumbnail(assets_dir: str, image_key: str):
    """Önce assets/ içinden yükle, yoksa placeholder üret. PIL yoksa None."""
    if not _PIL_AVAILABLE:
        return None
    path = os.path.join(assets_dir, f"{image_key}.png")
    if os.path.isfile(path):
        try:
            return Image.open(path).convert("RGB").resize((THUMB_W, THUMB_H))
        except Exception:
            pass
    return _placeholder_image(image_key)


class PlaneList(ttk.LabelFrame):
    """
    Uçaklar: sol thumbnail, sağda isim/kapasite/yakıt.
    İdeal satır yeşil çerçeve; altta 'Neden Seçildi?' metni.
    """

    def __init__(self, parent: tk.Misc, assets_dir: str = "", **kwargs):
        super().__init__(parent, text=" Uygun Uçaklar ", padding=8, **kwargs)
        self._assets_dir = assets_dir or self._default_assets_dir()
        self._inner: Optional[ttk.Frame] = None
        self._explanation_label: Optional[ttk.Label] = None
        self._photos: list = []  # referans tutulmalı

    @staticmethod
    def _default_assets_dir() -> str:
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

    def _build(self) -> None:
        self._inner = ttk.Frame(self)
        self._inner.pack(fill=tk.BOTH, expand=True)
        self._explanation_label = ttk.Label(self, text="", wraplength=400, font=("Helvetica Neue", 10))
        self._explanation_label.pack(anchor=tk.W, pady=(8, 0))

    def set_candidates(self, candidates: List[AircraftCandidate], explanation: str = "") -> None:
        """Listeyi güncelle; ideal satırı vurgula, açıklamayı yaz."""
        if self._inner is None:
            self._build()
        for w in self._inner.winfo_children():
            w.destroy()
        self._photos.clear()

        if not candidates:
            ttk.Label(self._inner, text="Bu sefer için uygun uçak yok.").pack(anchor=tk.W)
            if self._explanation_label:
                self._explanation_label.config(text="")
            return

        for c in candidates:
            is_ideal = c.is_ideal
            try:
                row_bg = "#d4edda" if is_ideal else (self._inner.cget("background") if self._inner.winfo_exists() else None)
            except Exception:
                row_bg = None
            row_bg = row_bg or ("#d4edda" if is_ideal else "#f0f0f0")
            row = tk.Frame(self._inner, bg=row_bg, padx=6, pady=4)
            row.pack(fill=tk.X, pady=2)
            # Thumbnail (PIL varsa)
            img = _load_thumbnail(self._assets_dir, c.aircraft.image_key or "plane")
            if img is not None and _PIL_AVAILABLE:
                photo = ImageTk.PhotoImage(img)
                self._photos.append(photo)
                lbl_img = tk.Label(row, image=photo, bg=row.cget("bg"))
                lbl_img.image = photo
                lbl_img.pack(side=tk.LEFT, padx=(0, 10))
            # Metin
            text = f"{c.aircraft.name}  ·  Kapasite: {c.aircraft.capacity}  ·  Yakıt: ~{int(round(c.total_fuel_liters))} L"
            font = ("Helvetica Neue", 11, "bold") if is_ideal else ("Helvetica Neue", 11)
            lbl_text = tk.Label(row, text=text, font=font, bg=row.cget("bg"))
            lbl_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

        if self._explanation_label:
            self._explanation_label.config(text=f"Neden Seçildi? {explanation}" if explanation else "")
