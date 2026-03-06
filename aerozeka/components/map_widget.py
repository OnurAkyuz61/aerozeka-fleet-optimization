# -*- coding: utf-8 -*-
"""Kalkış/varış marker ve aradaki rota çizgisi ile harita."""

import tkinter as tk
from typing import Optional

try:
    from tkintermapview import TkinterMapView
    _MAP_AVAILABLE = True
except ImportError:
    _MAP_AVAILABLE = False


class MapWidget(tk.Frame):
    """
    Harita: iki nokta için marker, aralarında path.
    Koordinat yoksa Türkiye merkezinde varsayılan konum.
    """

    def __init__(self, parent: tk.Misc, width: int = 400, height: int = 220, **kwargs):
        super().__init__(parent, **kwargs)
        self._width = width
        self._height = height
        self._markers = []
        self._path = None
        self._build()

    def _build(self) -> None:
        if _MAP_AVAILABLE:
            self._map = TkinterMapView(self, width=self._width, height=self._height, corner_radius=8)
            self._map.pack(fill=tk.BOTH, expand=True)
            self._map.set_position(39.0, 35.0)
            self._map.set_zoom(5)
        else:
            self._map = None
            lbl = tk.Label(self, text="Harita: tkintermapview yüklü değil.", fg="gray")
            lbl.pack(expand=True)

    def set_route(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        origin_label: str = "Kalkış",
        dest_label: str = "Varış",
    ) -> None:
        """Kalkış ve varış noktalarına marker koyar, araya çizgi çizer."""
        if not _MAP_AVAILABLE or self._map is None:
            return
        # Eski marker/path temizle
        for m in self._markers:
            try:
                self._map.delete(m)
            except Exception:
                pass
        self._markers.clear()
        if self._path is not None:
            try:
                self._map.delete(self._path)
            except Exception:
                pass
            self._path = None

        m1 = self._map.set_marker(origin_lat, origin_lon, text=origin_label)
        m2 = self._map.set_marker(dest_lat, dest_lon, text=dest_label)
        self._markers.extend([m1, m2])

        # Path: iki nokta arası çizgi (kütüphane destekliyorsa)
        try:
            self._path = self._map.set_path([(origin_lat, origin_lon), (dest_lat, dest_lon)])
        except Exception:
            pass

        # Haritayı rotayı gösterecek şekilde konumla
        mid_lat = (origin_lat + dest_lat) / 2
        mid_lon = (origin_lon + dest_lon) / 2
        self._map.set_position(mid_lat, mid_lon)
        self._map.set_zoom(5)

    def clear_route(self) -> None:
        """Marker ve path kaldır."""
        if not _MAP_AVAILABLE or self._map is None:
            return
        for m in self._markers:
            try:
                self._map.delete(m)
            except Exception:
                pass
        self._markers.clear()
        if self._path is not None:
            try:
                self._map.delete(self._path)
            except Exception:
                pass
            self._path = None
