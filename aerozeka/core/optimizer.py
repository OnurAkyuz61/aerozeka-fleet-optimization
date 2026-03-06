# -*- coding: utf-8 -*-
"""Kapasiteye göre uygun uçakları filtreler, en az yakıt harcayanı (en karlı) seçer."""

from typing import List

from .models import Flight, Aircraft, AircraftCandidate

# Yerel filo (resim anahtarı assets ile eşleşir)
FLEET: List[Aircraft] = [
    Aircraft("Boeing 737-800", "Boeing", 189, 3.2, "boeing737"),
    Aircraft("Boeing 737-700", "Boeing", 148, 2.8, "boeing737"),
    Aircraft("Airbus A320neo", "Airbus", 180, 2.6, "airbusa320"),
    Aircraft("Airbus A321", "Airbus", 220, 3.5, "airbusa320"),
    Aircraft("Airbus A319", "Airbus", 156, 2.5, "airbusa320"),
    Aircraft("Boeing 737-900", "Boeing", 220, 3.6, "boeing737"),
    Aircraft("Embraer E195", "Embraer", 124, 2.2, "airbusa320"),
]


class Optimizer:
    """Sefer için uygun uçakları ve en ideal seçimi hesaplar."""

    def __init__(self):
        self._fleet = FLEET.copy()

    def run(self, flight: Flight) -> tuple[List[AircraftCandidate], str]:
        """
        Kapasitesi yeten uçakları döndürür; en düşük toplam yakıt 'ideal' işaretlenir.
        İkinci dönüş: 'Neden Seçildi?' açıklama metni.
        """
        suitable: List[AircraftCandidate] = []
        for ac in self._fleet:
            if ac.capacity < flight.expected_passengers:
                continue
            total_fuel = flight.distance_km * ac.fuel_per_km
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
