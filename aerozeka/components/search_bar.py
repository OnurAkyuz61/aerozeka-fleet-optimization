# -*- coding: utf-8 -*-
"""Arama çubuğu ve Sefer Ara butonu (CustomTkinter)."""

import customtkinter as ctk
from typing import Callable, Optional


class SearchBar(ctk.CTkFrame):
    """Tek satır: CTkEntry + CTkButton, yuvarlak ve modern."""

    def __init__(self, parent: ctk.CTk, on_search: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_search = on_search or (lambda q: None)
        self._build()

    def _build(self) -> None:
        self.entry = ctk.CTkEntry(
            self,
            width=320,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=14),
            placeholder_text="TK2828 veya IST-TZX",
        )
        self.entry.pack(side="left", padx=(0, 12))
        self.entry.bind("<Return>", lambda e: self.trigger_search())

        self.btn = ctk.CTkButton(
            self,
            text="Sefer Ara",
            width=120,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.trigger_search,
        )
        self.btn.pack(side="left")

    def trigger_search(self) -> None:
        self._on_search(self.get_query().strip())

    def get_query(self) -> str:
        return self.entry.get() or ""

    def set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.entry.configure(state=state)
        self.btn.configure(state=state)
