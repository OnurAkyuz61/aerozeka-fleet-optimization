# -*- coding: utf-8 -*-
"""
FlightRadar24 API ile uçuş/rota verisi (koordinatlarla) çeker.
API eksik veya hata verirse koordinat simülasyonu ile güvenli fallback.
"""

import math
from typing import Optional

from .models import Flight

try:
    from FlightRadar24 import FlightRadar24API
    _FR24_AVAILABLE = True
except ImportError:
    _FR24_AVAILABLE = False

# Uçak tipi -> tahmini yolcu
_AIRCRAFT_CAPACITY = {
    "B738": 189, "B737": 148, "B739": 220, "A320": 180, "A321": 220,
    "A319": 156, "A20N": 180, "A21N": 220, "E195": 124, "B38M": 178,
}
_DEFAULT_KM = 800.0
_DEFAULT_PAX = 150

# Harita fallback: IATA -> (lat, lon)
_SIMULATED_COORDS = {
    "IST": (41.27, 28.75), "TZX": (41.00, 39.80), "ADB": (38.29, 27.15),
    "ESB": (40.12, 32.99), "AYT": (36.90, 30.80), "GZT": (36.95, 37.48),
    "SAW": (40.90, 29.31), "ADA": (36.98, 35.30), "VAN": (38.47, 43.33),
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _coords_for_route(origin_iata: str, dest_iata: str) -> tuple[float, float, float, float]:
    """Rota için kalkış/varış koordinatları (simülasyon)."""
    o = _SIMULATED_COORDS.get((origin_iata or "").upper().strip())
    d = _SIMULATED_COORDS.get((dest_iata or "").upper().strip())
    if o and d:
        return o[0], o[1], d[0], d[1]
    # Varsayılan: Türkiye merkezi civarı
    return 39.5, 32.5, 40.5, 34.0


class DataFetcher:
    """Uçuş verisi çekme: API + koordinat fallback."""

    def fetch(self, query: str) -> Optional[Flight]:
        """
        Sefer numarası (TK2828) veya rota (IST-TZX) ile uçuş döndürür.
        Koordinatlar API'den veya simülasyondan gelir; harita her zaman çalışır.
        """
        q = query.strip().upper().replace(" ", "")
        if not q:
            return None

        flight = self._fetch_from_api(q)
        if flight is None:
            flight = self._fetch_from_fallback(q)
        if flight is not None and (flight.origin_lat is None or flight.dest_lat is None):
            flight = self._ensure_coords(flight)
        return flight

    def _fetch_from_api(self, query: str) -> Optional[Flight]:
        if not _FR24_AVAILABLE:
            return None
        try:
            fr_api = FlightRadar24API()
            zones = fr_api.get_zones()
            zone = zones.get("world") or zones.get("europe") or list(zones.values())[0]
            bounds = fr_api.get_bounds(zone)
            flights = fr_api.get_flights(bounds=bounds)
            if not flights:
                return None

            is_route = "-" in query and len(query) >= 6
            want_orig, want_dest = (query.split("-", 1)[0].strip(), query.split("-", 1)[1].strip()) if is_route else (None, None)

            for fr in flights:
                callsign = getattr(fr, "callsign", "") or ""
                number = getattr(fr, "number", "") or ""
                orig_iata = getattr(fr, "origin_airport_iata", None) or ""
                dest_iata = getattr(fr, "destination_airport_iata", None) or ""

                if is_route:
                    if (orig_iata or "").upper() != want_orig or (dest_iata or "").upper() != want_dest:
                        continue
                else:
                    q_digits = "".join(c for c in query if c.isdigit())
                    num_str = "".join(c for c in (str(number) + (callsign or "").upper()) if c.isdigit())
                    if q_digits and num_str and q_digits not in num_str:
                        continue
                    if not q_digits and query not in (callsign or "").upper() and query not in (str(number) or "").upper():
                        continue

                try:
                    details = fr_api.get_flight_details(fr)
                    if details:
                        fr.set_flight_details(details)
                except Exception:
                    pass

                origin_name = getattr(fr, "origin_airport_name", None) or orig_iata or "?"
                dest_name = getattr(fr, "destination_airport_name", None) or dest_iata or "?"
                route_str = f"{orig_iata or '?'}-{dest_iata or '?'}"
                flight_number = (callsign or str(number) or query).strip()

                dist = _DEFAULT_KM
                olat, olon, dlat, dlon = None, None, None, None
                if hasattr(fr, "origin_airport_latitude") and getattr(fr, "origin_airport_latitude", None) is not None:
                    olat = getattr(fr, "origin_airport_latitude", None)
                    olon = getattr(fr, "origin_airport_longitude", None)
                    dlat = getattr(fr, "destination_airport_latitude", None)
                    dlon = getattr(fr, "destination_airport_longitude", None)
                    if None not in (olat, olon, dlat, dlon):
                        dist = _haversine_km(float(olat), float(olon), float(dlat), float(dlon))
                if olat is None:
                    olat, olon, dlat, dlon = _coords_for_route(orig_iata, dest_iata)
                    if dist == _DEFAULT_KM:
                        dist = _haversine_km(olat, olon, dlat, dlon)

                ac_type = getattr(fr, "aircraft_code", None)
                pax = _AIRCRAFT_CAPACITY.get((ac_type or "").strip().upper(), _DEFAULT_PAX)

                return Flight(
                    flight_number=flight_number,
                    route=route_str,
                    origin=str(origin_name),
                    destination=str(dest_name),
                    distance_km=round(dist, 1),
                    expected_passengers=pax,
                    origin_lat=float(olat) if olat is not None else None,
                    origin_lon=float(olon) if olon is not None else None,
                    dest_lat=float(dlat) if dlat is not None else None,
                    dest_lon=float(dlon) if dlon is not None else None,
                )
            return None
        except Exception:
            return None

    def _fetch_from_fallback(self, query: str) -> Optional[Flight]:
        """Yerel liste ile eşleşme (koordinatlar sonra eklenir)."""
        from aerozeka.data import find_flight_by_number, find_flight_by_route
        old = find_flight_by_number(query) or find_flight_by_route(query)
        if old is None:
            return None
        return Flight(
            flight_number=old.flight_number,
            route=old.route,
            origin=old.origin,
            destination=old.destination,
            distance_km=old.distance_km,
            expected_passengers=old.expected_passengers,
        )

    def _ensure_coords(self, flight: Flight) -> Flight:
        """Eksik koordinatları rota kodundan simüle et."""
        parts = flight.route.upper().replace(" ", "").split("-")
        orig_iata = parts[0] if len(parts) > 0 else ""
        dest_iata = parts[1] if len(parts) > 1 else ""
        olat, olon, dlat, dlon = _coords_for_route(orig_iata, dest_iata)
        return Flight(
            flight_number=flight.flight_number,
            route=flight.route,
            origin=flight.origin,
            destination=flight.destination,
            distance_km=flight.distance_km,
            expected_passengers=flight.expected_passengers,
            origin_lat=olat,
            origin_lon=olon,
            dest_lat=dlat,
            dest_lon=dlon,
        )
