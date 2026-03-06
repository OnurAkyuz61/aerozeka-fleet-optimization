# -*- coding: utf-8 -*-
"""
AeroZeka - Veri modülü.
Uçuş seferleri ve filo (uçak) verilerini tutar.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class Flight:
    """Sefer bilgisi."""
    flight_number: str
    route: str          # Örn: "IST-TZX"
    origin: str
    destination: str
    distance_km: float
    expected_passengers: int


@dataclass
class Aircraft:
    """Uçak modeli bilgisi."""
    name: str           # Örn: "Boeing 737-800"
    manufacturer: str   # Boeing / Airbus
    capacity: int       # Yolcu kapasitesi
    fuel_per_km: float  # km başına yakıt tüketimi (litre)


# --- Sefer verileri (gerçekçi örnekler) ---
FLIGHTS: List[Flight] = [
    Flight(
        flight_number="TK2828",
        route="IST-TZX",
        origin="İstanbul",
        destination="Trabzon",
        distance_km=900.0,
        expected_passengers=145,
    ),
    Flight(
        flight_number="TK2424",
        route="IST-ADB",
        origin="İstanbul",
        destination="İzmir",
        distance_km=325.0,
        expected_passengers=98,
    ),
    Flight(
        flight_number="TK2162",
        route="IST-ESB",
        origin="İstanbul",
        destination="Ankara",
        distance_km=350.0,
        expected_passengers=120,
    ),
    Flight(
        flight_number="TK4002",
        route="IST-AYT",
        origin="İstanbul",
        destination="Antalya",
        distance_km=475.0,
        expected_passengers=165,
    ),
    Flight(
        flight_number="TK2840",
        route="IST-GZT",
        origin="İstanbul",
        destination="Gaziantep",
        distance_km=1050.0,
        expected_passengers=110,
    ),
]

# --- Filo verileri (Boeing / Airbus) ---
AIRCRAFT: List[Aircraft] = [
    Aircraft(name="Boeing 737-800", manufacturer="Boeing", capacity=189, fuel_per_km=3.2),
    Aircraft(name="Boeing 737-700", manufacturer="Boeing", capacity=148, fuel_per_km=2.8),
    Aircraft(name="Airbus A320neo", manufacturer="Airbus", capacity=180, fuel_per_km=2.6),
    Aircraft(name="Airbus A321", manufacturer="Airbus", capacity=220, fuel_per_km=3.5),
    Aircraft(name="Airbus A319", manufacturer="Airbus", capacity=156, fuel_per_km=2.5),
    Aircraft(name="Boeing 737-900", manufacturer="Boeing", capacity=220, fuel_per_km=3.6),
    Aircraft(name="Embraer E195", manufacturer="Embraer", capacity=124, fuel_per_km=2.2),
]


def get_all_flights() -> List[Flight]:
    """Tüm seferleri döndürür."""
    return FLIGHTS.copy()


def get_all_aircraft() -> List[Aircraft]:
    """Tüm uçakları döndürür."""
    return AIRCRAFT.copy()


def find_flight_by_number(flight_number: str) -> Flight | None:
    """Sefer numarasına göre sefer bulur (büyük/küçük harf duyarsız)."""
    key = flight_number.strip().upper()
    for f in FLIGHTS:
        if f.flight_number.upper() == key:
            return f
    return None


def find_flight_by_route(route: str) -> Flight | None:
    """Rota kodu ile sefer bulur (örn: IST-TZX). Büyük/küçük harf duyarsız."""
    key = route.strip().upper().replace(" ", "")
    for f in FLIGHTS:
        if f.route.upper() == key:
            return f
    return None
