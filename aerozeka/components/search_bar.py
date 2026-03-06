# -*- coding: utf-8 -*-
"""Arama çubuğu ve Sefer Ara butonu."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class SearchBar(ttk.Frame):
    """Tek satır: Entry + buton. Arama tetiklenince callback çağrılır."""

    def __init__(self, parent: tk.Misc, on_search: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self._on_search = on_search or (lambda q: None)
        self._build()

    def _build(self) -> None:
        self.entry = ttk.Entry(self, width=36, font=("Helvetica Neue", 12))
        self.entry.pack(side=tk.LEFT, padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self.trigger_search())
        self.btn = ttk.Button(self, text="Sefer Ara", command=self.trigger_search)
        self.btn.pack(side=tk.LEFT)

    def trigger_search(self) -> None:
        self._on_search(self.get_query().strip())

    def get_query(self) -> str:
        return self.entry.get() or ""

    def set_busy(self, busy: bool) -> None:
        state = tk.DISABLED if busy else tk.NORMAL
        self.entry.config(state=state)
        self.btn.config(state=state)
