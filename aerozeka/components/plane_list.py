# -*- coding: utf-8 -*-
"""Uçak listesi: CTkFrame kartlar. Resim yoksa gri placeholder (çökme yok)."""

import os
from typing import List, Optional

import customtkinter as ctk

from aerozeka.core import AircraftCandidate

THUMB_W, THUMB_H = 44, 44
CARD_CORNER = 10
IDEAL_FG = "#2ecc71"
CARD_FG = ("gray28", "gray22")
# Resim bulunamadığında kullanılacak gri placeholder (assets içinde)
PLACEHOLDER_FILENAME = "placeholder_plane.png"


def _thumbnail_path(assets_dir: str, image_key: str) -> Optional[str]:
    """Varsa resim dosya yolu, yoksa None."""
    if not image_key:
        return None
    path = os.path.join(assets_dir, f"{image_key}.png")
    return path if os.path.isfile(path) else None


def _placeholder_plane_path(assets_dir: str) -> Optional[str]:
    """Gri uçak placeholder resmi; yoksa None."""
    path = os.path.join(assets_dir, PLACEHOLDER_FILENAME)
    return path if os.path.isfile(path) else None


class PlaneList(ctk.CTkFrame):
    """
    Uygun uçaklar: alt alta CTkFrame kartlar.
    Koyu gri kartlar, beyaz metin; en ideal kart yeşil (#2ecc71), siyah metin.
    """

    def __init__(self, parent: ctk.CTk, assets_dir: str = "", **kwargs):
        super().__init__(
            parent,
            corner_radius=10,
            fg_color=("gray25", "gray20"),
            **kwargs,
        )
        self._assets_dir = assets_dir or self._default_assets_dir()
        self._scroll: Optional[ctk.CTkScrollableFrame] = None
        self._explanation_label: Optional[ctk.CTkLabel] = None
        self._image_refs: list = []

    @staticmethod
    def _default_assets_dir() -> str:
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

    def _build(self) -> None:
        if self._scroll is not None:
            return
        header = ctk.CTkLabel(
            self,
            text="Uygun Uçaklar",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray90", "gray90"),
        )
        header.pack(anchor="w", padx=16, pady=(16, 10))

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        self._explanation_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=("gray70", "gray70"),
            wraplength=340,
            justify="left",
        )
        self._explanation_label.pack(anchor="w", padx=16, pady=(8, 16))

    def set_candidates(self, candidates: List[AircraftCandidate], explanation: str = "") -> None:
        if self._scroll is None:
            self._build()
        for w in self._scroll.winfo_children():
            w.destroy()
        self._image_refs.clear()

        if not candidates:
            ctk.CTkLabel(
                self._scroll,
                text="Bu sefer için uygun uçak yok.",
                text_color=("gray60", "gray60"),
            ).pack(anchor="w", pady=8)
            if self._explanation_label:
                self._explanation_label.configure(text="")
            return

        for c in candidates:
            is_ideal = c.is_ideal
            fg = IDEAL_FG if is_ideal else CARD_FG
            text_color = "black" if is_ideal else ("gray90", "gray90")

            card = ctk.CTkFrame(
                self._scroll,
                corner_radius=CARD_CORNER,
                fg_color=fg,
                height=72,
            )
            card.pack(fill="x", pady=4)
            card.pack_propagate(False)

            # Sol: uçak resmi veya gri placeholder (resim yoksa/hatada çökme yok)
            thumb_path = _thumbnail_path(self._assets_dir, c.aircraft.image_key or "plane")
            if not thumb_path:
                thumb_path = _placeholder_plane_path(self._assets_dir)
            img_ok = False
            if thumb_path:
                try:
                    img = ctk.CTkImage(light_image=thumb_path, dark_image=thumb_path, size=(THUMB_W, THUMB_H))
                    self._image_refs.append(img)
                    ctk.CTkLabel(card, text="", image=img).pack(side="left", padx=12, pady=14)
                    img_ok = True
                except Exception:
                    pass
            if not img_ok:
                _icon_label(card, c.aircraft.name, text_color).pack(side="left", padx=12, pady=14)

            # Sağ: isim, kapasite, yakıt
            line1 = f"{c.aircraft.name}"
            line2 = f"Kapasite: {c.aircraft.capacity}  ·  Tahmini yakıt: ~{int(round(c.total_fuel_liters))} L"
            font_title = ctk.CTkFont(size=14, weight="bold")
            font_sub = ctk.CTkFont(size=12)

            right = ctk.CTkFrame(card, fg_color="transparent")
            right.pack(side="left", fill="both", expand=True, padx=(0, 16), pady=12)
            ctk.CTkLabel(right, text=line1, font=font_title, text_color=text_color).pack(anchor="w")
            ctk.CTkLabel(right, text=line2, font=font_sub, text_color=text_color).pack(anchor="w")

        if self._explanation_label:
            self._explanation_label.configure(
                text=f"Neden Seçildi? {explanation}" if explanation else ""
            )


def _icon_label(parent: ctk.CTkFrame, name: str, text_color: str) -> ctk.CTkLabel:
    """Resim yoksa kısa metin ikonu (örn. B737)."""
    short = name[:4].upper() if name else "✈"
    return ctk.CTkLabel(
        parent,
        text=short,
        width=THUMB_W,
        height=THUMB_H,
        font=ctk.CTkFont(size=11, weight="bold"),
        text_color=text_color,
        fg_color=("gray35", "gray30"),
        corner_radius=8,
    )
