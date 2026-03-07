# -*- coding: utf-8 -*-
"""
FlightRadar24 API ile uçuş/rota verisi (koordinatlarla) çeker.
API timeout/bağlantı hatasında çökme yok; yerel liste ve rota fallback devreye girer.
"""

import math
from typing import Optional

from .models import Flight

try:
    from FlightRadar24 import FlightRadar24API
    _FR24_AVAILABLE = True
except ImportError:
    _FR24_AVAILABLE = False

# geopy opsiyonel; yoksa Haversine kullanılır
try:
    from geopy.distance import geodesic as _geodesic
    _GEOPY_AVAILABLE = True
except ImportError:
    _GEOPY_AVAILABLE = False

# Uçak tipi -> tahmini yolcu
_AIRCRAFT_CAPACITY = {
    "B738": 189, "B737": 148, "B739": 220, "A320": 180, "A321": 220,
    "A319": 156, "A20N": 180, "A21N": 220, "E195": 124, "B38M": 178,
}
_DEFAULT_KM = 800.0
_DEFAULT_PAX = 150

# Geniş havalimanları sözlüğü: IATA -> (enlem, boylam, isim)
# API hata/veri yoksa rota fallback; sözlükte yoksa "Sefer bulunamadı"
POPULAR_AIRPORTS: dict[str, tuple[float, float, str]] = {
    "IST": (41.2753, 28.7519, "İstanbul"),
    "SAW": (40.8986, 29.3092, "İstanbul Sabiha Gökçen"),
    "TZX": (41.0027, 39.7892, "Trabzon"),
    "ADB": (38.2924, 27.1569, "İzmir"),
    "ESB": (40.1281, 32.9951, "Ankara Esenboğa"),
    "AYT": (36.8987, 30.8005, "Antalya"),
    "GZT": (36.9472, 37.4789, "Gaziantep"),
    "ADA": (36.9822, 35.2804, "Adana"),
    "VAN": (38.4682, 43.3322, "Van"),
    "SFO": (37.6189, -122.3750, "San Francisco"),
    "JFK": (40.6398, -73.7787, "New York JFK"),
    "LAX": (33.9425, -118.4081, "Los Angeles"),
    "LHR": (51.4700, -0.4543, "Londra Heathrow"),
    "CDG": (49.0097, 2.5478, "Paris Charles de Gaulle"),
    "FRA": (50.0379, 8.5622, "Frankfurt"),
    "AMS": (52.3105, 4.7683, "Amsterdam"),
    "DXB": (25.2532, 55.3657, "Dubai"),
    "MUC": (48.3538, 11.7750, "Münih"),
    "ZRH": (47.4647, 8.5492, "Zürih"),
    "VIE": (48.1103, 16.5697, "Viyana"),
    "SVO": (55.9726, 37.4146, "Moskova Sheremetyevo"),
    "DME": (55.4086, 37.9061, "Moskova Domodedovo"),
    "ORD": (41.9742, -87.9073, "Chicago O'Hare"),
    "MIA": (25.7959, -80.2870, "Miami"),
    "ATL": (33.6367, -84.4281, "Atlanta"),
    "BCN": (41.2971, 2.0785, "Barcelona"),
    "MAD": (40.4983, -3.5676, "Madrid"),
    "FCO": (41.8003, 12.2389, "Roma Fiumicino"),
    "LIS": (38.7813, -9.1359, "Lizbon"),
    "CPT": (-33.9715, 18.6021, "Cape Town"),
    "NRT": (35.7720, 140.3929, "Tokyo Narita"),
    "HKG": (22.3080, 113.9185, "Hong Kong"),
    "SIN": (1.3644, 103.9915, "Singapur"),
}

# Eski simülasyon koordinatları (geriye uyumluluk): IATA -> (lat, lon)
_SIMULATED_COORDS = {k.upper(): (v[0], v[1]) for k, v in POPULAR_AIRPORTS.items()}
# Rota fallback için büyük harf anahtarlı sözlük
_AIRPORTS_UPPER = {k.upper(): v for k, v in POPULAR_AIRPORTS.items()}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """İki koordinat arası mesafe (km) – Haversine formülü."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Mesafe (km): geopy varsa geodesic, yoksa Haversine."""
    if _GEOPY_AVAILABLE:
        try:
            return float(_geodesic((lat1, lon1), (lat2, lon2)).kilometers)
        except Exception:
            pass
    return _haversine_km(lat1, lon1, lat2, lon2)


def _coords_for_route(origin_iata: str, dest_iata: str) -> tuple[float, float, float, float]:
    """Rota için kalkış/varış koordinatları (popüler havalimanları sözlüğünden)."""
    o = _SIMULATED_COORDS.get((origin_iata or "").upper().strip())
    d = _SIMULATED_COORDS.get((dest_iata or "").upper().strip())
    if o and d:
        return o[0], o[1], d[0], d[1]
    return 39.5, 32.5, 40.5, 34.0


class DataFetcher:
    """Uçuş verisi çekme: API + koordinat fallback."""

    def fetch(self, query: str) -> Optional[Flight]:
        """
        Sefer numarası (TK2828) veya rota (IST-SFO) ile uçuş döndürür.
        Sıra: API -> yerel liste -> rota fallback (popüler havalimanları + Haversine).
        Sadece sözlükte olmayan rota/veri girilirse None (Sefer bulunamadı).
        """
        q = query.strip().upper().replace(" ", "")
        if not q:
            return None

        flight = self._fetch_from_api(q)
        if flight is None:
            flight = self._fetch_from_fallback(q)
        if flight is None and self._is_route_format(q):
            flight = self._fetch_from_route_fallback(q)
        if flight is not None and (flight.origin_lat is None or flight.dest_lat is None):
            flight = self._ensure_coords(flight)
        return flight

    @staticmethod
    def _is_route_format(query: str) -> bool:
        """Örn: IST-SFO gibi ORIG-DEST formatında mı?"""
        if "-" not in query or len(query) < 6:
            return False
        parts = query.split("-", 1)
        return len(parts) == 2 and len(parts[0]) >= 2 and len(parts[1]) >= 2

    def _fetch_from_route_fallback(self, query: str) -> Optional[Flight]:
        """
        API ve yerel liste sonuç vermediğinde: rota (ORIG-DEST) popüler havalimanları
        sözlüğünde varsa mesafe (Haversine) ve koordinatlarla Flight döndürür.
        Her iki kod da sözlükte olmalı; yoksa None (Sefer bulunamadı).
        """
        parts = query.split("-", 1)
        orig_code = (parts[0] or "").strip()
        dest_code = (parts[1] or "").strip()
        if not orig_code or not dest_code:
            return None

        orig_info = _AIRPORTS_UPPER.get(orig_code)
        dest_info = _AIRPORTS_UPPER.get(dest_code)
        if not orig_info or not dest_info:
            return None

        olat, olon, origin_name = orig_info
        dlat, dlon, dest_name = dest_info
        distance_km = _distance_km(olat, olon, dlat, dlon)
        route_str = f"{orig_code}-{dest_code}"

        return Flight(
            flight_number=route_str,
            route=route_str,
            origin=origin_name,
            destination=dest_name,
            distance_km=round(distance_km, 1),
            expected_passengers=_DEFAULT_PAX,
            origin_lat=olat,
            origin_lon=olon,
            dest_lat=dlat,
            dest_lon=dlon,
        )

    def _fetch_from_api(self, query: str) -> Optional[Flight]:
        """API çağrıları try-except ile sarılı; timeout/ConnectionError'da çökme yok."""
        if not _FR24_AVAILABLE:
            return None
        try:
            try:
                fr_api = FlightRadar24API(timeout=15)
            except TypeError:
                fr_api = FlightRadar24API()
        except Exception:
            return None
        try:
            zones = fr_api.get_zones()
            zone = zones.get("world") or zones.get("europe") or list(zones.values())[0]
            bounds = fr_api.get_bounds(zone)
            flights = fr_api.get_flights(bounds=bounds)
        except (TimeoutError, ConnectionError, OSError, Exception):
            return None
        if not flights:
            return None

        is_route = "-" in query and len(query) >= 6
        want_orig, want_dest = (query.split("-", 1)[0].strip(), query.split("-", 1)[1].strip()) if is_route else (None, None)

        try:
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
        except (TimeoutError, ConnectionError, OSError, Exception):
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
