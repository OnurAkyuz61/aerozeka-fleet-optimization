# -*- coding: utf-8 -*-
"""
AeroZeka ana penceresi: CustomTkinter, hata toleranslı (traceback yerine şık mesaj).
"""

import threading

import customtkinter as ctk

from aerozeka.core import DataFetcher, Optimizer, DemandPredictor
from aerozeka.components import SearchBar, MapWidget, FlightInfo, PlaneList
from aerozeka.assets import ensure_placeholders

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def _show_message(parent: ctk.CTk, title: str, message: str, is_warning: bool = False) -> None:
    """
    Sistem pop-up yerine CTk penceresi ile kullanıcı dostu mesaj.
    Traceback göstermez; başlık ve metin şık bir toplevel'da.
    """
    win = ctk.CTkToplevel(parent)
    win.title(title)
    win.geometry("420x180")
    win.transient(parent)
    win.grab_set()
    frame = ctk.CTkFrame(win, fg_color=("gray22", "gray17"), corner_radius=12)
    frame.pack(fill="both", expand=True, padx=20, pady=20)
    ctk.CTkLabel(
        frame, text=message,
        font=ctk.CTkFont(size=13),
        text_color=("gray90", "gray90"),
        wraplength=360,
        justify="left",
    ).pack(pady=(20, 16), padx=20, anchor="w")
    btn = ctk.CTkButton(frame, text="Tamam", width=100, command=win.destroy)
    btn.pack(pady=(0, 20))
    win.after(100, win.focus_force)


class App(ctk.CTk):
    """Ana uygulama: hata durumunda çökme yok, UI donmaz."""

    def __init__(self):
        super().__init__()
        ensure_placeholders()
        self.title("AeroZeka — Filo Atama")
        self.minsize(780, 660)
        self.geometry("860x700")

        self._fetcher = DataFetcher()
        self._optimizer = Optimizer()
        self._demand_predictor = DemandPredictor()
        self._searching = False
        self._status_label: ctk.CTkLabel | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=24, pady=24)

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
        # Girdi SearchBar'da temizlendi; boşsa uyarı ver, işlem başlatma
        if not query or not str(query).strip():
            _show_message(self, "Bilgi", "Lütfen sefer numarası veya rota girin (örn: TK2828, IST-TZX).")
            return
        if self._searching:
            return
        self._searching = True
        self._search_bar.set_busy(True)
        if self._status_label:
            self._status_label.configure(text="Aranıyor...")

        def run():
            try:
                flight = self._fetcher.fetch(query)
                self.after(0, lambda: self._on_result(query, flight))
            except Exception:
                self.after(0, lambda: self._on_result(query, None))

        threading.Thread(target=run, daemon=True).start()

    def _on_result(self, query: str, flight) -> None:
        self._searching = False
        self._search_bar.set_busy(False)
        if self._status_label:
            self._status_label.configure(text="")

        try:
            if flight is None:
                _show_message(
                    self,
                    "Sefer bulunamadı",
                    "Sefer bulunamadı. Lütfen geçerli bir rota girin (örn: IST-TZX, IST-SFO).",
                    is_warning=True,
                )
                return

            # ML: model varsa tahmin, yoksa mesafe bazlı fallback (model_kullanildi=False)
            predicted = self._demand_predictor.predict(flight.distance_km)
            if predicted is not None:
                flight.expected_passengers = max(40, min(350, predicted))
                flight.ml_predicted = True
            else:
                flight.expected_passengers = DemandPredictor.estimate_from_distance(flight.distance_km)
                flight.ml_predicted = False

            self._flight_info.set_flight(flight)
            if flight.origin_lat is not None and flight.dest_lat is not None:
                self._map.set_route(
                    flight.origin_lat, flight.origin_lon,
                    flight.dest_lat, flight.dest_lon,
                    origin_label=(flight.origin or "")[:20],
                    dest_label=(flight.destination or "")[:20],
                )
            else:
                self._map.clear_route()

            candidates, explanation = self._optimizer.run(flight)
            if getattr(flight, "ml_predicted", False):
                pax = flight.expected_passengers
                ml_intro = f"Yapay zeka modelimiz bu rotadaki mevsimsel verilere dayanarak {pax} yolcu öngörmüştür. "
                explanation = ml_intro + explanation
            self._plane_list.set_candidates(candidates, explanation)

        except Exception:
            _show_message(
                self,
                "Hata",
                "Bir hata oluştu. Lütfen geçerli bir rota (örn: IST-TZX) ile tekrar deneyin.",
                is_warning=True,
            )

    def run(self) -> None:
        self.mainloop()


def run_app() -> None:
    app = App()
    app.run()
