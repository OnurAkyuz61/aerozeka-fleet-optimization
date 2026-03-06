# -*- coding: utf-8 -*-
"""
AeroZeka - Arayüz modülü.
Tkinter/ttk ile arama, sefer kartı, uygun uçak listesi ve en ideal seçim arayüzü.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from aerozeka.data import find_flight_by_number, find_flight_by_route
from aerozeka.optimization import get_suitable_aircraft, get_ideal_explanation


# --- Sabitler ---
APP_TITLE = "AeroZeka — Filo Atama"
FONT_HEADING = ("Helvetica Neue", 16, "bold")
FONT_BODY = ("Helvetica Neue", 12)
FONT_SMALL = ("Helvetica Neue", 11)
CARD_PAD = 16
LIST_ROW_HEIGHT = 28


def setup_styles(root: tk.Tk) -> ttk.Style:
    """macOS uyumlu ttk stilleri."""
    style = ttk.Style(root)
    try:
        style.theme_use("aqua")  # macOS yerel görünüm
    except tk.TclError:
        style.theme_use("default")
    style.configure("Card.TFrame", background="#f0f4f8")
    style.configure("Card.TLabel", background="#f0f4f8", font=FONT_BODY)
    style.configure("CardTitle.TLabel", background="#f0f4f8", font=("Helvetica Neue", 13, "bold"))
    style.configure("Ideal.TLabel", background="#d4edda", font=("Helvetica Neue", 11, "bold"))
    style.configure("Explanation.TLabel", background="#f8f9fa", font=FONT_SMALL, wraplength=620)
    return style


class AeroZekaApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.minsize(680, 520)
        self.root.geometry("720x580")

        setup_styles(self.root)

        self._build_ui()
        self._flight_card_frame: ttk.Frame | None = None
        self._table_frame: ttk.Frame | None = None
        self._explanation_label: ttk.Label | None = None
        self._tree: ttk.Treeview | None = None

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=24)
        main.pack(fill=tk.BOTH, expand=True)

        # --- Başlık ---
        title = ttk.Label(main, text="AeroZeka", font=FONT_HEADING)
        title.pack(pady=(0, 8))
        subtitle = ttk.Label(main, text="Sefer numarası veya rota ile arama yapın (örn: TK2828 veya IST-TZX)")
        subtitle.pack(pady=(0, 20))

        # --- Arama satırı ---
        search_frame = ttk.Frame(main)
        search_frame.pack(fill=tk.X, pady=(0, 20))
        self.entry = ttk.Entry(search_frame, width=40, font=FONT_BODY)
        self.entry.pack(side=tk.LEFT, padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self._on_search())
        btn = ttk.Button(search_frame, text="Sefer Ara", command=self._on_search)
        btn.pack(side=tk.LEFT)

        # --- Sonuç alanı (kart + tablo + açıklama) ---
        self.result_frame = ttk.Frame(main)
        self.result_frame.pack(fill=tk.BOTH, expand=True)

    def _clear_results(self):
        if self._flight_card_frame:
            self._flight_card_frame.destroy()
            self._flight_card_frame = None
        if self._table_frame:
            self._table_frame.destroy()
            self._table_frame = None
        if self._explanation_label:
            self._explanation_label.destroy()
            self._explanation_label = None
        self._tree = None

    def _on_search(self):
        query = self.entry.get().strip()
        if not query:
            messagebox.showinfo("Bilgi", "Lütfen sefer numarası veya rota girin (örn: TK2828 veya IST-TZX).")
            return

        flight = find_flight_by_number(query) or find_flight_by_route(query)
        self._clear_results()

        if not flight:
            messagebox.showwarning("Sonuç yok", f"'{query}' için sefer bulunamadı.")
            return

        self._show_flight_card(flight)
        candidates = get_suitable_aircraft(flight)
        self._show_aircraft_table(flight, candidates)
        self._show_explanation(flight, candidates)

    def _show_flight_card(self, flight):
        card = ttk.LabelFrame(self.result_frame, text=" Sefer Bilgileri ", padding=CARD_PAD)
        card.pack(fill=tk.X, pady=(0, 16))
        self._flight_card_frame = card

        ttk.Label(card, text=f"Rota: {flight.route} ({flight.origin} → {flight.destination})").pack(anchor=tk.W)
        ttk.Label(card, text=f"Mesafe: {int(flight.distance_km)} km").pack(anchor=tk.W)
        ttk.Label(card, text=f"Beklenen Yolcu Sayısı: {flight.expected_passengers}").pack(anchor=tk.W)

    def _show_aircraft_table(self, flight, candidates):
        table_frame = ttk.Frame(self.result_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
        self._table_frame = table_frame

        ttk.Label(table_frame, text="Uygun Uçaklar", font=("Helvetica Neue", 12, "bold")).pack(anchor=tk.W, pady=(0, 6))

        if not candidates:
            ttk.Label(table_frame, text="Bu yolcu sayısını karşılayabilecek uçak bulunamadı.").pack(anchor=tk.W)
            return

        columns = ("uçak", "üretici", "kapasite", "yakıt_litre")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=min(12, len(candidates) + 1))
        tree.heading("uçak", text="Uçak")
        tree.heading("üretici", text="Üretici")
        tree.heading("kapasite", text="Kapasite")
        tree.heading("yakıt_litre", text="Toplam Yakıt (L)")

        tree.column("uçak", width=180)
        tree.column("üretici", width=100)
        tree.column("kapasite", width=80)
        tree.column("yakıt_litre", width=120)

        scroll = ttk.Scrollbar(table_frame)
        tree.configure(yscrollcommand=scroll.set)
        scroll.configure(command=tree.yview)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        for c in candidates:
            ac = c.aircraft
            fuel_str = f"{int(round(c.total_fuel_liters))} L"
            tag = "ideal" if c.is_ideal else ""
            tree.insert("", tk.END, values=(ac.name, ac.manufacturer, ac.capacity, fuel_str), tags=(tag,))

        tree.tag_configure("ideal", background="#d4edda", font=("Helvetica Neue", 11, "bold"))
        self._tree = tree

    def _show_explanation(self, flight, candidates):
        text = get_ideal_explanation(flight, candidates)
        if not text:
            return
        box = ttk.LabelFrame(self.result_frame, text=" Neden İdeal? ", padding=10)
        box.pack(fill=tk.X, pady=(0, 8))
        self._explanation_label = box
        lbl = ttk.Label(box, text=text, wraplength=620)
        lbl.pack(anchor=tk.W, fill=tk.X)

    def run(self):
        self.root.mainloop()


def run_app() -> None:
    """Uygulamayı başlatır."""
    app = AeroZekaApp()
    app.run()
