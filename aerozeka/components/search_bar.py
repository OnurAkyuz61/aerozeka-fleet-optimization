# -*- coding: utf-8 -*-
"""
Havayolu tarzı dinamik arama: Uçuş Numarası / Güzergah seçimi,
TK prefix’li uçuş no veya kalkış/varış combobox ile backend’e TK2828 / IST-JFK gönderir.
"""

import re
import customtkinter as ctk
from typing import Callable, Optional

try:
    from aerozeka.core.data_fetcher import POPULAR_AIRPORTS
except ImportError:
    POPULAR_AIRPORTS = {}

# Radyo değerleri
MODE_FLIGHT = "ucus_numarasi"
MODE_ROUTE = "guzergah"

# Havalimanı combobox için "IATA - Şehir" listesi (sözlükten türetilir)
def _airport_display_list() -> list[str]:
    return sorted(
        [f"{iata} - {info[2]}" for iata, info in POPULAR_AIRPORTS.items()],
        key=lambda x: x.upper(),
    )


def _iata_from_display(display: str) -> str:
    """'IST - İstanbul' -> 'IST' (ilk 3 karakter IATA)."""
    if not display or " - " not in display:
        return (display or "").strip()[:3].upper()
    return display.split(" - ", 1)[0].strip().upper()[:3]


def normalize_query(raw: str) -> str:
    """Backend uyumu: büyük harf, boşluksuz."""
    if not raw or not isinstance(raw, str):
        return ""
    return raw.strip().upper().replace(" ", "")


class SearchBar(ctk.CTkFrame):
    """
    Dinamik arama: Radyo ile 'Uçuş Numarası' veya 'Güzergah' seçilir.
    - Uçuş Numarası: TK + rakam girişi -> backend'e TK2828
    - Güzergah: İki CTkComboBox (Kalkış/Varış) -> backend'e IST-JFK
    """

    def __init__(self, parent: ctk.CTk, on_search: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_search = on_search or (lambda q: None)
        self._mode = ctk.StringVar(value=MODE_ROUTE)
        self._flight_frame: Optional[ctk.CTkFrame] = None
        self._route_frame: Optional[ctk.CTkFrame] = None
        self._btn: Optional[ctk.CTkButton] = None
        self._airport_values = _airport_display_list()
        self._build()

    def _build(self) -> None:
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(anchor="center", pady=(0, 0))

        # ---- Radyo: Uçuş Numarası | Güzergah (varsayılan: Güzergah) ----
        radio_frame = ctk.CTkFrame(inner, fg_color="transparent")
        radio_frame.pack(pady=(0, 12))

        r1 = ctk.CTkRadioButton(
            radio_frame,
            text="Uçuş Numarası",
            variable=self._mode,
            value=MODE_FLIGHT,
            font=ctk.CTkFont(size=13),
            command=self._on_mode_change,
            radiobutton_width=20,
            radiobutton_height=20,
        )
        r1.pack(side="left", padx=(0, 24))

        r2 = ctk.CTkRadioButton(
            radio_frame,
            text="Güzergah",
            variable=self._mode,
            value=MODE_ROUTE,
            font=ctk.CTkFont(size=13),
            command=self._on_mode_change,
            radiobutton_width=20,
            radiobutton_height=20,
        )
        r2.pack(side="left")

        # ---- Form alanı (seçime göre değişir) ----
        self._form_container = ctk.CTkFrame(inner, fg_color="transparent")
        self._form_container.pack(pady=(0, 12))

        self._build_flight_form()
        self._build_route_form()

        # ---- Ortak "Sefer Ara" butonu ----
        self._btn = ctk.CTkButton(
            inner,
            text="Sefer Ara",
            width=140,
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.trigger_search,
        )
        self._btn.pack(pady=(4, 0))

        self._on_mode_change()

    def _build_flight_form(self) -> None:
        """Uçuş Numarası: [TK] + sadece rakam girişi."""
        self._flight_frame = ctk.CTkFrame(self._form_container, fg_color="transparent")
        # Entry + TK etiketi yan yana (TK tıklanamaz sabit)
        row = ctk.CTkFrame(self._flight_frame, fg_color="transparent")
        row.pack()

        tk_label = ctk.CTkLabel(
            row,
            text="TK",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=("gray75", "gray70"),
            width=36,
            height=40,
            fg_color=("gray28", "gray24"),
            corner_radius=8,
        )
        tk_label.pack(side="left", padx=(0, 8))
        tk_label.bind("<Button-1>", lambda e: None)

        self._flight_entry = ctk.CTkEntry(
            row,
            width=160,
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=14),
            placeholder_text="2828",
        )
        self._flight_entry.pack(side="left")
        self._flight_entry.bind("<Return>", lambda e: self.trigger_search())
        self._flight_entry.bind("<KeyRelease>", self._validate_digits)

    def _validate_digits(self, event=None) -> None:
        """Sadece rakam bırak; diğer karakterleri sil."""
        s = self._flight_entry.get()
        digits = re.sub(r"\D", "", s)
        if digits != s:
            self._flight_entry.delete(0, "end")
            self._flight_entry.insert(0, digits)

    def _build_route_form(self) -> None:
        """Güzergah: Kalkış ve Varış CTkComboBox yan yana (IATA - Şehir)."""
        self._route_frame = ctk.CTkFrame(self._form_container, fg_color="transparent")
        left_col = ctk.CTkFrame(self._route_frame, fg_color="transparent")
        left_col.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(
            left_col, text="Kalkış", font=ctk.CTkFont(size=12), text_color=("gray70", "gray65")
        ).pack(anchor="w", pady=(0, 4))
        self._combo_origin = ctk.CTkComboBox(
            left_col,
            values=self._airport_values,
            width=200,
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=13),
        )
        self._combo_origin.pack(anchor="w")
        if self._airport_values:
            self._combo_origin.set(self._airport_values[0])
        right_col = ctk.CTkFrame(self._route_frame, fg_color="transparent")
        right_col.pack(side="left")
        ctk.CTkLabel(
            right_col, text="Varış", font=ctk.CTkFont(size=12), text_color=("gray70", "gray65")
        ).pack(anchor="w", pady=(0, 4))
        self._combo_dest = ctk.CTkComboBox(
            right_col,
            values=self._airport_values,
            width=200,
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=13),
        )
        self._combo_dest.pack(anchor="w")
        if len(self._airport_values) > 1:
            self._combo_dest.set(self._airport_values[1])
        self._combo_dest.bind("<Return>", lambda e: self.trigger_search())

    def _on_mode_change(self) -> None:
        """Radyo değişince form alanını göster/gizle; varsayılan Güzergah."""
        if self._flight_frame is None or self._route_frame is None:
            return
        if self._mode.get() == MODE_FLIGHT:
            self._route_frame.pack_forget()
            self._flight_frame.pack()
            self._flight_entry.focus_set()
        else:
            self._flight_frame.pack_forget()
            self._route_frame.pack()
            try:
                self._combo_origin.focus_set()
            except Exception:
                pass

    def _get_query_flight(self) -> str:
        """Uçuş numarası modu: TK + sadece rakamlar."""
        digits = re.sub(r"\D", "", self._flight_entry.get())
        return f"TK{digits}" if digits else ""

    def _get_query_route(self) -> str:
        """Güzergah modu: ORIG-DEST (IATA 3 harf)."""
        o = _iata_from_display(self._combo_origin.get())
        d = _iata_from_display(self._combo_dest.get())
        if not o or not d:
            return ""
        return f"{o}-{d}"

    def get_cleaned_query(self) -> str:
        """Backend'e gidecek metin: TK2828 veya IST-JFK."""
        if self._mode.get() == MODE_FLIGHT:
            return self._get_query_flight()
        return normalize_query(self._get_query_route())

    def get_query(self) -> str:
        """Ham girdi yerine temizlenmiş sorgu (geriye uyumluluk)."""
        return self.get_cleaned_query()

    def trigger_search(self) -> None:
        cleaned = self.get_cleaned_query()
        self._on_search(cleaned)

    def set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self._flight_entry.configure(state=state)
        self._combo_origin.configure(state=state)
        self._combo_dest.configure(state=state)
        if self._btn:
            self._btn.configure(state=state)
