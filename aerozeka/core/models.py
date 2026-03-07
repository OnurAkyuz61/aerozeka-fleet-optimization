# -*- coding: utf-8 -*-
"""Ortak veri modelleri."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Flight:
    """Sefer: rota, mesafe, yolcu ve harita için koordinatlar."""
    flight_number: str
    route: str
    origin: str
    destination: str
    distance_km: float
    expected_passengers: int
    # Harita için; API vermezse simülasyonla doldurulur
    origin_lat: Optional[float] = None
    origin_lon: Optional[float] = None
    dest_lat: Optional[float] = None
    dest_lon: Optional[float] = None
    # ML yolcu tahmini kullanıldıysa True (UI'da "ML Tahmini" gösterilir)
    ml_predicted: bool = False

    @property
    def duration_minutes(self) -> int:
        """Tahmini uçuş süresi (dakika): ortalama 800 km/h varsayımı."""
        if self.distance_km <= 0:
            return 0
        return int(round(self.distance_km / 800.0 * 60))


@dataclass
class Aircraft:
    """Filo uçağı."""
    name: str
    manufacturer: str
    capacity: int
    fuel_per_km: float
    image_key: str = ""  # assets eşlemesi: boeing737, airbusa320 vb.


@dataclass
class AircraftCandidate:
    """Sefer için uygun aday; toplam yakıt ve ideal mi bilgisi."""
    aircraft: Aircraft
    total_fuel_liters: float
    is_ideal: bool
