# -*- coding: utf-8 -*-
"""Mesafe, tahmini yolcu, uçuş süresi bilgi kartı."""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from aerozeka.core import Flight


class FlightInfo(ttk.LabelFrame):
    """Sefer detayları: rota, mesafe (km), yolcu, süre."""

    def __init__(self, parent: tk.Misc, **kwargs):
        super().__init__(parent, text=" Sefer Bilgileri ", padding=12, **kwargs)
        self._labels = {}
        self._build()

    def _build(self) -> None:
        for key, text in [
            ("route", "Rota: -"),
            ("distance", "Mesafe: - km"),
            ("passengers", "Tahmini yolcu: -"),
            ("duration", "Tahmini uçuş süresi: -"),
        ]:
            lbl = ttk.Label(self, text=text)
            lbl.pack(anchor=tk.W)
            self._labels[key] = lbl

    def set_flight(self, flight: Optional[Flight]) -> None:
        if flight is None:
            self._labels["route"].config(text="Rota: -")
            self._labels["distance"].config(text="Mesafe: - km")
            self._labels["passengers"].config(text="Tahmini yolcu: -")
            self._labels["duration"].config(text="Tahmini uçuş süresi: -")
            return
        self._labels["route"].config(text=f"Rota: {flight.route} ({flight.origin} → {flight.destination})")
        self._labels["distance"].config(text=f"Mesafe: {int(flight.distance_km)} km")
        self._labels["passengers"].config(text=f"Tahmini yolcu: {flight.expected_passengers}")
        self._labels["duration"].config(text=f"Tahmini uçuş süresi: {flight.duration_minutes} dk")
