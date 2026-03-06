# -*- coding: utf-8 -*-
"""
AeroZeka ana penceresi: CustomTkinter ile koyu tema, yuvarlak frame'ler.
"""

import threading
from tkinter import messagebox

import customtkinter as ctk

from aerozeka.core import DataFetcher, Optimizer
from aerozeka.components import SearchBar, MapWidget, FlightInfo, PlaneList
from aerozeka.assets import ensure_placeholders

# Tema (pencere oluşturulmadan önce)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    """Ana uygulama: CTk pencere + bileşen orkestrasyonu."""

    def __init__(self):
        super().__init__()
        ensure_placeholders()
        self.title("AeroZeka — Filo Atama")
        self.minsize(780, 660)
        self.geometry("860x700")

        self._fetcher = DataFetcher()
        self._optimizer = Optimizer()
        self._searching = False
        self._status_label: ctk.CTkLabel | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        # Ana container: padding, koyu arka plan
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=24, pady=24)

        # Başlık
        ctk.CTkLabel(
            main, text="AeroZeka",
            font=ctk.CTkFont(family="Helvetica Neue", size=24, weight="bold"),
            text_color=("gray90", "gray90"),
        ).pack(pady=(0, 4))
        ctk.CTkLabel(
            main, text="Sefer numarası veya rota girin (örn: TK2828, IST-TZX)",
            font=ctk.CTkFont(size=13),
            text_color=("gray70", "gray70"),
        ).pack(pady=(0, 16))

        self._search_bar = SearchBar(main, on_search=self._on_search)
        self._search_bar.pack(fill="x", pady=(0, 12))

        self._status_label = ctk.CTkLabel(
            main, text="",
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray60"),
        )
        self._status_label.pack(pady=(0, 16))

        content = ctk.CTkFrame(main, fg_color="transparent")
        content.pack(fill="both", expand=True)

        left = ctk.CTkFrame(content, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0, 16))
        self._flight_info = FlightInfo(left)
        self._flight_info.pack(fill="x", pady=(0, 12))
        self._map = MapWidget(left, width=400, height=240)
        self._map.pack(fill="both", expand=True, pady=(0, 12))

        right = ctk.CTkFrame(content, fg_color="transparent")
        right.pack(side="right", fill="both", expand=True)
        self._plane_list = PlaneList(right)
        self._plane_list.pack(fill="both", expand=True)

    def _on_search(self, query: str) -> None:
        if not query:
            messagebox.showinfo("Bilgi", "Lütfen sefer numarası veya rota girin.")
            return
        if self._searching:
            return
        self._searching = True
        self._search_bar.set_busy(True)
        if self._status_label:
            self._status_label.configure(text="Aranıyor...")

        def run():
            flight = self._fetcher.fetch(query)
            self.after(0, lambda: self._on_result(query, flight))

        threading.Thread(target=run, daemon=True).start()

    def _on_result(self, query: str, flight) -> None:
        self._searching = False
        self._search_bar.set_busy(False)
        if self._status_label:
            self._status_label.configure(text="")

        if flight is None:
            messagebox.showwarning("Sonuç yok", f"'{query}' için sefer bulunamadı.")
            return

        self._flight_info.set_flight(flight)
        if flight.origin_lat is not None and flight.dest_lat is not None:
            self._map.set_route(
                flight.origin_lat, flight.origin_lon,
                flight.dest_lat, flight.dest_lon,
                origin_label=flight.origin[:20],
                dest_label=flight.destination[:20],
            )
        else:
            self._map.clear_route()

        candidates, explanation = self._optimizer.run(flight)
        self._plane_list.set_candidates(candidates, explanation)

    def run(self) -> None:
        self.mainloop()


def run_app() -> None:
    app = App()
    app.run()
