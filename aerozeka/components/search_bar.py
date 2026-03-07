# -*- coding: utf-8 -*-
"""Arama çubuğu ve Sefer Ara butonu (CustomTkinter). Girdi doğrulama ve temizleme."""

import customtkinter as ctk
from typing import Callable, Optional


def normalize_query(raw: str) -> str:
    """
    Kullanıcı girdisini temizler: baş/son boşluk silinir, büyük harf, aradaki boşluklar kaldırılır.
    Örn: ' ist-sfo ' -> 'IST-SFO'
    """
    if not raw or not isinstance(raw, str):
        return ""
    return raw.strip().upper().replace(" ", "")


class SearchBar(ctk.CTkFrame):
    """Tek satır: CTkEntry + CTkButton. Temizlenmiş ve doğrulanmış girdi ile arama."""

    def __init__(self, parent: ctk.CTk, on_search: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_search = on_search or (lambda q: None)
        self._build()

    def _build(self) -> None:
        # İçerik (Entry + Buton) ortalanmış bir frame içinde; ana ekranda dengeli görünüm
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(anchor="center", pady=(0, 0))

        self.entry = ctk.CTkEntry(
            inner,
            width=320,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=14),
            placeholder_text="TK2828 veya IST-TZX",
        )
        self.entry.pack(side="left", padx=(0, 12))
        self.entry.bind("<Return>", lambda e: self.trigger_search())

        self.btn = ctk.CTkButton(
            inner,
            text="Sefer Ara",
            width=120,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.trigger_search,
        )
        self.btn.pack(side="left")

    def trigger_search(self) -> None:
        """
        Girdiyi temizleyip doğrular. Boşsa callback'i çağırmaz (main tarafında boş için uyarı gösterilir).
        """
        cleaned = self.get_cleaned_query()
        self._on_search(cleaned)

    def get_query(self) -> str:
        """Ham girdi (temizlenmemiş)."""
        return self.entry.get() or ""

    def get_cleaned_query(self) -> str:
        """Temizlenmiş girdi: büyük harf, boşluksuz (örn: IST-SFO)."""
        return normalize_query(self.get_query())

    def set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.entry.configure(state=state)
        self.btn.configure(state=state)
