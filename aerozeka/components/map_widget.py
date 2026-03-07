# -*- coding: utf-8 -*-
"""Kalkış/varış marker ve rota çizgisi; CartoDB Dark Matter. Rota sonrası otomatik odaklanma."""

import math
import customtkinter as ctk
from typing import Optional

try:
    from tkintermapview import TkinterMapView
    _MAP_AVAILABLE = True
except ImportError:
    _MAP_AVAILABLE = False

CARTO_DARK_TILES = "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"


def _zoom_for_distance_km(distance_km: float) -> int:
    """Mesafe (km) için her iki markerın da görüneceği zoom seviyesi (1=uzak, 6=yakın)."""
    if distance_km <= 0:
        return 5
    if distance_km >= 10000:
        return 1
    if distance_km >= 5000:
        return 2
    if distance_km >= 2500:
        return 3
    if distance_km >= 1000:
        return 4
    if distance_km >= 400:
        return 5
    return 6


class MapWidget(ctk.CTkFrame):
    """
    Harita: iki nokta marker, arada path.
    CartoDB Dark Matter ile koyu tema.
    """

    def __init__(self, parent: ctk.CTk, width: int = 400, height: int = 220, **kwargs):
        super().__init__(parent, corner_radius=10, fg_color=("gray22", "gray17"), **kwargs)
        self._width = width
        self._height = height
        self._markers: list = []
        self._path = None
        self._build()

    def _build(self) -> None:
        if _MAP_AVAILABLE:
            self._map = TkinterMapView(
                self,
                width=self._width,
                height=self._height,
                corner_radius=10,
            )
            self._map.pack(fill="both", expand=True)
            self._map.set_position(39.0, 35.0)
            self._map.set_zoom(5)
            try:
                self._map.set_tile_server(CARTO_DARK_TILES)
            except Exception:
                pass
        else:
            self._map = None
            ctk.CTkLabel(
                self,
                text="Harita: tkintermapview yüklü değil.",
                text_color=("gray50", "gray50"),
            ).pack(expand=True)

    def set_route(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        origin_label: str = "Kalkış",
        dest_label: str = "Varış",
    ) -> None:
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

        m1 = self._map.set_marker(origin_lat, origin_lon, text=origin_label)
        m2 = self._map.set_marker(dest_lat, dest_lon, text=dest_label)
        self._markers.extend([m1, m2])

        try:
            self._path = self._map.set_path([(origin_lat, origin_lon), (dest_lat, dest_lon)])
        except Exception:
            pass

        # Her iki markerı da gösterecek şekilde ortala ve zoom (kıtalararası için uzaklaş)
        mid_lat = (origin_lat + dest_lat) / 2
        mid_lon = (origin_lon + dest_lon) / 2
        self._map.set_position(mid_lat, mid_lon)
        # Yaklaşık mesafe (km) ile zoom: 10.000+ km -> zoom 1, kısa rota -> zoom 5-6
        approx_km = 111.0 * math.sqrt(
            (origin_lat - dest_lat) ** 2 + ((origin_lon - dest_lon) * math.cos(math.radians(mid_lat))) ** 2
        )
        zoom = _zoom_for_distance_km(approx_km)
        self._map.set_zoom(zoom)

    def clear_route(self) -> None:
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
