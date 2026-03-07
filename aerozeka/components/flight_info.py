# -*- coding: utf-8 -*-
"""Mesafe, tahmini yolcu, uçuş süresi bilgi kartı (CustomTkinter)."""

import customtkinter as ctk
from typing import Optional

from aerozeka.core import Flight


class FlightInfo(ctk.CTkFrame):
    """Sefer detayları: koyu kart, beyaz/açık metin, yuvarlak köşe."""

    def __init__(self, parent: ctk.CTk, **kwargs):
        super().__init__(
            parent,
            corner_radius=10,
            fg_color=("gray25", "gray20"),
            **kwargs,
        )
        self._labels: dict = {}
        self._build()

    def _build(self) -> None:
        header = ctk.CTkLabel(
            self,
            text="Sefer Bilgileri",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("gray90", "gray90"),
        )
        header.pack(anchor="w", padx=16, pady=(16, 10))

        for key, text in [
            ("route", "Rota: -"),
            ("distance", "Mesafe: - km"),
            ("passengers", "Tahmini yolcu: -"),
            ("duration", "Tahmini uçuş süresi: -"),
        ]:
            lbl = ctk.CTkLabel(
                self,
                text=text,
                font=ctk.CTkFont(size=13),
                text_color=("gray85", "gray85"),
            )
            pady = (2, 16) if key == "duration" else 2
            lbl.pack(anchor="w", padx=16, pady=pady)
            self._labels[key] = lbl

    def set_flight(self, flight: Optional[Flight]) -> None:
        if flight is None:
            self._labels["route"].configure(text="Rota: -")
            self._labels["distance"].configure(text="Mesafe: - km")
            self._labels["passengers"].configure(text="Tahmini yolcu: -")
            self._labels["duration"].configure(text="Tahmini uçuş süresi: -")
            return
        self._labels["route"].configure(text=f"Rota: {flight.route} ({flight.origin} → {flight.destination})")
        self._labels["distance"].configure(text=f"Mesafe: {int(flight.distance_km)} km")
        pax_text = f"Tahmini yolcu: {flight.expected_passengers}"
        if getattr(flight, "ml_predicted", False):
            pax_text += "  (ML Tahmini)"
        self._labels["passengers"].configure(text=pax_text)
        self._labels["duration"].configure(text=f"Tahmini uçuş süresi: {flight.duration_minutes} dk")
