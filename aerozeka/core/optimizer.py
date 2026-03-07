# -*- coding: utf-8 -*-
"""Kapasite ve menzile göre uygun uçakları filtreler; en az yakıt harcayan (en karlı) seçilir."""

from typing import List

from .models import Flight, Aircraft, AircraftCandidate

# THY filo verisi data.ucaklar tek kaynaktır; core Aircraft (image_key ile) buradan türetilir
try:
    from aerozeka.data import ucaklar as _ucaklar
except ImportError:
    _ucaklar = []


def _image_key_for_manufacturer(manufacturer: str) -> str:
    """UI asset eşlemesi: boeing737 / airbusa320."""
    return "boeing737" if manufacturer == "Boeing" else "airbusa320"


def _build_fleet() -> List[Aircraft]:
    """ucaklar sözlük listesinden core.models.Aircraft filo listesi oluşturur."""
    fleet: List[Aircraft] = []
    for u in _ucaklar:
        name = u["id"]
        manufacturer = "Boeing" if "Boeing" in name else ("Airbus" if "Airbus" in name else "Diğer")
        fleet.append(
            Aircraft(
                name=name,
                manufacturer=manufacturer,
                capacity=u["kapasite"],
                fuel_per_km=u["yakit_tuketimi_km"],
                image_key=_image_key_for_manufacturer(manufacturer),
                menzil_km=u["menzil_km"],
            )
        )
    return fleet


FLEET: List[Aircraft] = _build_fleet()


class Optimizer:
    """Sefer için uygun uçakları ve en ideal seçimi hesaplar."""

    def __init__(self):
        self._fleet = FLEET.copy()

    def run(self, flight: Flight) -> tuple[List[AircraftCandidate], str]:
        """
        Uygun uçakları iki kurala göre filtreler; menzili veya kapasitesi yetmeyen listede yer almaz.
        - ucak["kapasite"] >= sefer beklenen yolcu
        - ucak["menzil_km"] >= sefer mesafe_km (menzili yetmeyen uçak kesinlikle dahil edilmez)
        En düşük toplam yakıt tüketeni 'ideal' olarak işaretlenir.
        """
        suitable: List[AircraftCandidate] = []
        mesafe_km = flight.distance_km
        beklenen_yolcu = flight.expected_passengers

        for ac in self._fleet:
            if ac.capacity < beklenen_yolcu:
                continue
            if ac.menzil_km < mesafe_km:
                continue
            total_fuel = mesafe_km * ac.fuel_per_km
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
