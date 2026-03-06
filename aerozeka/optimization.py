# -*- coding: utf-8 -*-
"""
AeroZeka - Optimizasyon modülü.
Kapasiteye göre uygun uçakları filtreler ve en düşük yakıt maliyetli uçağı seçer.
"""

from dataclasses import dataclass
from typing import List

from aerozeka.data import Flight, Aircraft, get_all_aircraft


@dataclass
class AircraftCandidate:
    """Sefer için uygun uçak adayı; toplam yakıt ve ideal olup olmadığı bilgisiyle."""
    aircraft: Aircraft
    total_fuel_liters: float
    is_ideal: bool


def get_suitable_aircraft(flight: Flight) -> List[AircraftCandidate]:
    """
    Seferin beklenen yolcu sayısını karşılayabilen uçakları döndürür.
    Toplam yakıt (litre) hesaplanır; en düşük yakıt tüketen 'En İdeal Uçak' olarak işaretlenir.
    """
    all_planes = get_all_aircraft()
    suitable: List[AircraftCandidate] = []

    for ac in all_planes:
        if ac.capacity < flight.expected_passengers:
            continue
        total_fuel = flight.distance_km * ac.fuel_per_km
        suitable.append(AircraftCandidate(aircraft=ac, total_fuel_liters=total_fuel, is_ideal=False))

    if not suitable:
        return suitable

    min_fuel = min(c.total_fuel_liters for c in suitable)
    for c in suitable:
        if c.total_fuel_liters == min_fuel:
            c.is_ideal = True
            break

    return sorted(suitable, key=lambda x: x.total_fuel_liters)


def get_ideal_explanation(flight: Flight, candidates: List[AircraftCandidate]) -> str:
    """
    'Neden İdeal?' açıklama metnini üretir.
    En ideal uçak yoksa boş string döner.
    """
    ideal = next((c for c in candidates if c.is_ideal), None)
    if not ideal:
        return ""

    dist = int(flight.distance_km)
    pax = flight.expected_passengers
    fuel = int(round(ideal.total_fuel_liters))
    name = ideal.aircraft.name

    return (
        f"Sistem Analizi: Beklenen {pax} yolcuyu karşılayabilecek kapasiteye sahip uçaklar arasından, "
        f"{flight.route} rotasındaki {dist} km'lik uçuş için en az yakıtı ({fuel} Litre) bu uçak tüketeceği için "
        f"şirket karını maksimize edecek en iyi seçim budur."
    )
