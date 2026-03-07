# -*- coding: utf-8 -*-
"""Kapasite ve menzile göre uygun uçakları filtreler, en az yakıt harcayanı (en karlı) seçer."""

from typing import List

from .models import Flight, Aircraft, AircraftCandidate

# Yerel filo: name, manufacturer, capacity, fuel_per_km, image_key, menzil_km
FLEET: List[Aircraft] = [
    # Dar gövde (kısa/orta menzil)
    Aircraft("Boeing 737-800", "Boeing", 189, 3.2, "boeing737", 5765),
    Aircraft("Boeing 737-700", "Boeing", 148, 2.8, "boeing737", 6230),
    Aircraft("Airbus A320neo", "Airbus", 180, 2.6, "airbusa320", 6500),
    Aircraft("Airbus A321", "Airbus", 220, 3.5, "airbusa320", 5950),
    Aircraft("Airbus A319", "Airbus", 156, 2.5, "airbusa320", 6850),
    Aircraft("Boeing 737-900", "Boeing", 220, 3.6, "boeing737", 5925),
    Aircraft("Embraer E195", "Embraer", 124, 2.2, "airbusa320", 4260),
    # Geniş gövde (kıtalararası, 12.000+ km menzil)
    Aircraft("Boeing 777-300ER", "Boeing", 396, 6.8, "boeing737", 13650),
    Aircraft("Airbus A350-900", "Airbus", 366, 5.9, "airbusa320", 15000),
    Aircraft("Boeing 787-9 Dreamliner", "Boeing", 296, 5.2, "boeing737", 14140),
]


class Optimizer:
    """Sefer için uygun uçakları ve en ideal seçimi hesaplar."""

    def __init__(self):
        self._fleet = FLEET.copy()

    def run(self, flight: Flight) -> tuple[List[AircraftCandidate], str]:
        """
        Hem kapasitesi hem menzili (menzil_km >= sefer mesafesi) yeten uçakları döndürür;
        en düşük toplam yakıt 'ideal' işaretlenir.
        """
        suitable: List[AircraftCandidate] = []
        distance_km = flight.distance_km
        for ac in self._fleet:
            if ac.capacity < flight.expected_passengers:
                continue
            # Menzil kontrolü: uçağın menzili sefer mesafesine yetmeli (menzil_km=0 ise kontrol yapılmaz)
            if ac.menzil_km > 0 and ac.menzil_km < distance_km:
                continue
            total_fuel = distance_km * ac.fuel_per_km
            suitable.append(AircraftCandidate(aircraft=ac, total_fuel_liters=total_fuel, is_ideal=False))

        if not suitable:
            return [], ""

        min_fuel = min(c.total_fuel_liters for c in suitable)
        for c in suitable:
            if c.total_fuel_liters == min_fuel:
                c.is_ideal = True
                break

        suitable.sort(key=lambda x: x.total_fuel_liters)
        explanation = self._explain(flight, suitable)
        return suitable, explanation

    def _explain(self, flight: Flight, candidates: List[AircraftCandidate]) -> str:
        ideal = next((c for c in candidates if c.is_ideal), None)
        if not ideal:
            return ""
        dist = int(flight.distance_km)
        pax = flight.expected_passengers
        fuel = int(round(ideal.total_fuel_liters))
        return (
            f"Beklenen {pax} yolcuyu karşılayabilecek uçaklar arasında, {flight.route} rotasındaki "
            f"{dist} km uçuş için en az yakıt ({fuel} L) bu uçakta tüketildiği için en karlı seçimdir."
        )
