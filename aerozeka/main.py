# -*- coding: utf-8 -*-
"""
AeroZeka ana penceresi: sadece pencere ve ana frame; bileşenleri yükler ve birbirine bağlar.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading

from aerozeka.core import DataFetcher, Optimizer
from aerozeka.components import SearchBar, MapWidget, FlightInfo, PlaneList
from aerozeka.assets import ensure_placeholders


class App:
    """Ana uygulama: pencere + bileşen orkestrasyonu."""

    def __init__(self):
        ensure_placeholders()
        self.root = tk.Tk()
        self.root.title("AeroZeka — Filo Atama")
        self.root.minsize(720, 620)
        self.root.geometry("800x650")

        self._fetcher = DataFetcher()
        self._optimizer = Optimizer()
        self._searching = False
        self._status_label: tk.Label | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="AeroZeka", font=("Helvetica Neue", 18, "bold")).pack(pady=(0, 4))
        ttk.Label(main, text="Sefer numarası veya rota girin (örn: TK2828, IST-TZX)").pack(pady=(0, 12))

        self._search_bar = SearchBar(main, on_search=self._on_search)
        self._search_bar.pack(fill=tk.X, pady=(0, 16))

        self._status_label = ttk.Label(main, text="", font=("Helvetica Neue", 11))
        self._status_label.pack(pady=(0, 8))

        content = ttk.Frame(main)
        content.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(content)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))
        self._flight_info = FlightInfo(left)
        self._flight_info.pack(fill=tk.X, pady=(0, 10))
        self._map = MapWidget(left, width=380, height=220)
        self._map.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        right = ttk.Frame(content)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self._plane_list = PlaneList(right)
        self._plane_list.pack(fill=tk.BOTH, expand=True)

    def _on_search(self, query: str) -> None:
        if not query:
            messagebox.showinfo("Bilgi", "Lütfen sefer numarası veya rota girin.")
            return
        if self._searching:
            return
        self._searching = True
        self._search_bar.set_busy(True)
        if self._status_label:
            self._status_label.config(text="Aranıyor...")

        def run():
            flight = self._fetcher.fetch(query)
            self.root.after(0, lambda: self._on_result(query, flight))

        threading.Thread(target=run, daemon=True).start()

    def _on_result(self, query: str, flight) -> None:
        self._searching = False
        self._search_bar.set_busy(False)
        if self._status_label:
            self._status_label.config(text="")

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
        self.root.mainloop()


def run_app() -> None:
    App().run()
