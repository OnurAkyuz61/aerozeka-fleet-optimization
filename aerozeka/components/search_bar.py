# -*- coding: utf-8 -*-
"""
Havayolu tarzı dinamik arama: Uçuş Numarası / Güzergah seçimi,
TK prefix’li uçuş no veya kalkış/varış combobox ile backend’e TK2828 / IST-JFK gönderir.
Güzergah: CTkEntry + yüzen CTkScrollableFrame ile gerçek autocomplete (yazdıkça liste, tıklayınca seçim).
"""

import re
import customtkinter as ctk
from typing import Callable, List, Optional

try:
    from aerozeka.core.data_fetcher import POPULAR_AIRPORTS
except ImportError:
    POPULAR_AIRPORTS = {}

# Radyo değerleri
MODE_FLIGHT = "ucus_numarasi"
MODE_ROUTE = "guzergah"

# Havalimanı combobox için "IATA - Şehir" listesi (sözlükten türetilir)
def _airport_display_list() -> List[str]:
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


# Autocomplete dropdown yüksekliği
_AUTOCOMPLETE_DROPDOWN_HEIGHT = 120


class SearchBar(ctk.CTkFrame):
    """
    Dinamik arama: Radyo ile 'Uçuş Numarası' veya 'Güzergah' seçilir.
    - Uçuş Numarası: TK + rakam girişi -> backend'e TK2828
    - Güzergah: İki CTkEntry + yüzen liste (autocomplete) -> backend'e IST-JFK
    """

    def __init__(self, parent: ctk.CTk, on_search: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_search = on_search or (lambda q: None)
        self._mode = ctk.StringVar(value=MODE_ROUTE)
        self._flight_frame: Optional[ctk.CTkFrame] = None
        self._route_frame: Optional[ctk.CTkFrame] = None
        self._btn: Optional[ctk.CTkButton] = None
        # Ana havalimanı listesi (autocomplete filtrelemede kullanılır; değiştirilmez)
        self._airport_master_list: List[str] = _airport_display_list()
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
        """Güzergah: Kalkış ve Varış CTkEntry + yüzen CTkScrollableFrame (autocomplete)."""
        self._route_frame = ctk.CTkFrame(self._form_container, fg_color="transparent")
        # --- Kalkış (Entry + yüzen liste) ---
        left_col = ctk.CTkFrame(self._route_frame, fg_color="transparent")
        left_col.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(
            left_col, text="Kalkış", font=ctk.CTkFont(size=12), text_color=("gray70", "gray65")
        ).pack(anchor="w", pady=(0, 4))
        self._entry_origin = ctk.CTkEntry(
            left_col,
            width=200,
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            placeholder_text="Örn: IST veya İstanbul",
        )
        self._entry_origin.pack(anchor="w")
        self._entry_origin.bind("<KeyRelease>", lambda e: self._on_autocomplete_key("origin", e))
        self._entry_origin.bind("<Return>", lambda e: self.trigger_search())
        self._entry_origin.bind("<FocusOut>", lambda e: self._schedule_maybe_close_dropdown("origin"))
        self._dropdown_origin = ctk.CTkScrollableFrame(
            left_col, fg_color=("gray22", "gray18"), height=_AUTOCOMPLETE_DROPDOWN_HEIGHT, width=200
        )
        self._dropdown_origin.pack(anchor="w", pady=(2, 0))
        self._dropdown_origin.pack_forget()

        # --- Varış (Entry + yüzen liste) ---
        right_col = ctk.CTkFrame(self._route_frame, fg_color="transparent")
        right_col.pack(side="left")
        ctk.CTkLabel(
            right_col, text="Varış", font=ctk.CTkFont(size=12), text_color=("gray70", "gray65")
        ).pack(anchor="w", pady=(0, 4))
        self._entry_dest = ctk.CTkEntry(
            right_col,
            width=200,
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            placeholder_text="Örn: JFK veya New York",
        )
        self._entry_dest.pack(anchor="w")
        self._entry_dest.bind("<KeyRelease>", lambda e: self._on_autocomplete_key("dest", e))
        self._entry_dest.bind("<Return>", lambda e: self.trigger_search())
        self._entry_dest.bind("<FocusOut>", lambda e: self._schedule_maybe_close_dropdown("dest"))
        self._dropdown_dest = ctk.CTkScrollableFrame(
            right_col, fg_color=("gray22", "gray18"), height=_AUTOCOMPLETE_DROPDOWN_HEIGHT, width=200
        )
        self._dropdown_dest.pack(anchor="w", pady=(2, 0))
        self._dropdown_dest.pack_forget()

    def _filter_airports_by_query(self, query: str) -> List[str]:
        """Ana listeden yazılan metne göre eşleşenleri döndürür (içinde geçiyor, büyük/küçük harf duyarsız)."""
        if not query or not query.strip():
            return list(self._airport_master_list)
        q = query.strip().lower()
        return [s for s in self._airport_master_list if q in s.lower()]

    def _dropdown_for(self, which: str):
        """'origin' veya 'dest' için ilgili dropdown frame."""
        return self._dropdown_origin if which == "origin" else self._dropdown_dest

    def _entry_for(self, which: str):
        """'origin' veya 'dest' için ilgili entry."""
        return self._entry_origin if which == "origin" else self._entry_dest

    def _hide_dropdown(self, which: str) -> None:
        """Yüzen listeyi gizler."""
        self._dropdown_for(which).pack_forget()

    def _show_dropdown(self, which: str) -> None:
        """Yüzen listeyi görünür yapar."""
        self._dropdown_for(which).pack(anchor="w", pady=(2, 0))

    def _populate_dropdown(self, which: str, matches: List[str]) -> None:
        """Dropdown içeriğini temizleyip eşleşen her havalimanı için tıklanabilir buton ekler."""
        frame = self._dropdown_for(which)
        for w in frame.winfo_children():
            w.destroy()
        for text in matches:
            btn = ctk.CTkButton(
                frame,
                text=text,
                font=ctk.CTkFont(size=12),
                fg_color="transparent",
                text_color=("gray90", "gray90"),
                hover_color=("gray35", "gray30"),
                anchor="w",
                height=32,
                corner_radius=6,
                command=(lambda t: (lambda: self._on_autocomplete_select(which, t)))(text),
            )
            btn.pack(fill="x", pady=1, padx=4)

    def _on_autocomplete_select(self, which: str, display_text: str) -> None:
        """Kullanıcı listeden bir havalimanı seçti: entry'yi güncelle, listeyi kapat."""
        entry = self._entry_for(which)
        entry.delete(0, "end")
        entry.insert(0, display_text)
        self._hide_dropdown(which)
        entry.focus_set()

    def _on_autocomplete_key(self, which: str, event) -> None:
        """KeyRelease: 2+ karakterde eşleşen varsa listeyi göster ve doldur; yoksa veya <2 karakterde gizle."""
        try:
            entry = self._entry_for(which)
            text = (entry.get() or "").strip()
            if len(text) < 2:
                self._hide_dropdown(which)
                return
            matches = self._filter_airports_by_query(text)
            if not matches:
                self._hide_dropdown(which)
                return
            self._populate_dropdown(which, matches)
            self._show_dropdown(which)
        except Exception:
            self._hide_dropdown(which)

    def _schedule_maybe_close_dropdown(self, which: str) -> None:
        """FocusOut sonrası kısa gecikmeyle listeyi kapat (odak dropdown dışındaysa)."""
        def maybe_close():
            try:
                root = self.winfo_toplevel()
                w = root.focus_get() if hasattr(root, "focus_get") else None
                dropdown = self._dropdown_for(which)
                entry = self._entry_for(which)
                if w is None:
                    self._hide_dropdown(which)
                    return
                # Odak bu dropdown veya içindeki bir widget üzerinde mi?
                p = w
                while p:
                    if p == dropdown:
                        return
                    p = getattr(p, "master", None)
                if w != entry:
                    self._hide_dropdown(which)
            except Exception:
                pass
        self.after(150, maybe_close)

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
                self._entry_origin.focus_set()
            except Exception:
                pass

    def _get_query_flight(self) -> str:
        """Uçuş numarası modu: TK + sadece rakamlar."""
        digits = re.sub(r"\D", "", self._flight_entry.get())
        return f"TK{digits}" if digits else ""

    def _get_query_route(self) -> str:
        """Güzergah modu: ORIG-DEST (IATA 3 harf)."""
        o = _iata_from_display(self._entry_origin.get())
        d = _iata_from_display(self._entry_dest.get())
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
        self._entry_origin.configure(state=state)
        self._entry_dest.configure(state=state)
        if self._btn:
            self._btn.configure(state=state)
