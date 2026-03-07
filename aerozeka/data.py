# -*- coding: utf-8 -*-
"""
AeroZeka - Veri modülü.
Uçuş seferleri ve filo (uçak) verileri. FlightRadar24 API ile anlık/planlanmış uçuş çekme
ve API'nin vermediği mesafe/yolcu için tahmin mantığı.
"""

from dataclasses import dataclass
from typing import List, Optional
import math

# FlightRadar24 API (API key gerekmez) - opsiyonel
try:
    from FlightRadar24 import FlightRadar24API
    _FR24_AVAILABLE = True
except ImportError:
    _FR24_AVAILABLE = False


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
    menzil_km: int = 0  # Maksimum uçuş menzili (km); 0 = kontrol yapılmaz


# --- Uçak tipi (ICAO) -> tahmini yolcu kapasitesi (simülasyon) ---
# API mesafe/yolcu vermediğinde kullanılır
_AIRCRAFT_TYPE_CAPACITY: dict[str, int] = {
    "B738": 189, "B737": 148, "B739": 220, "B77W": 386, "B788": 242,
    "A320": 180, "A321": 220, "A319": 156, "A20N": 180, "A21N": 220,
    "E195": 124, "E190": 114, "AT72": 78, "B38M": 178,
}

# --- Rota (origin-dest IATA) veya mesafe tahmini için kısa mesafe (km) ---
# Bilinmeyen rotalar için varsayılan ortalama
_DEFAULT_DISTANCE_KM = 800.0
_DEFAULT_PASSENGERS = 150


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """İki koordinat arası mesafe (km)."""
    R = 6371.0  # Dünya yarıçapı km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _estimate_passengers_from_aircraft_type(aircraft_type: Optional[str]) -> int:
    """Uçak tipine göre tahmini yolcu sayısı. Örn: B738 -> 189."""
    if not aircraft_type:
        return _DEFAULT_PASSENGERS
    key = (aircraft_type or "").strip().upper()
    return _AIRCRAFT_TYPE_CAPACITY.get(key, _DEFAULT_PASSENGERS)


def _distance_from_flight_details(fr_flight) -> float:
    """set_flight_details sonrası uçuş nesnesindeki origin/destination koordinatlarıyla mesafe (km)."""
    try:
        olat = getattr(fr_flight, "origin_airport_latitude", None)
        olon = getattr(fr_flight, "origin_airport_longitude", None)
        dlat = getattr(fr_flight, "destination_airport_latitude", None)
        dlon = getattr(fr_flight, "destination_airport_longitude", None)
        if None not in (olat, olon, dlat, dlon):
            return _haversine_km(float(olat), float(olon), float(dlat), float(dlon))
    except (TypeError, ValueError):
        pass
    return _DEFAULT_DISTANCE_KM


def fetch_flight_from_api(query: str) -> Optional[Flight]:
    """
    FlightRadar24 API (API key gerektirmez) ile uçuş numarası veya rota bilgisine göre
    anlık/planlanmış uçuş verisi çeker. Mesafe veya yolcu API'de yoksa tahmin edilir.

    - query: Uçuş numarası (örn: TK2828) veya rota (örn: IST-TZX).
    - Dönen: AeroZeka Flight nesnesi veya bulunamazsa/API yoksa None.
    """
    if not _FR24_AVAILABLE:
        return None

    query = query.strip().upper().replace(" ", "")
    if not query:
        return None

    try:
        fr_api = FlightRadar24API()
        zones = fr_api.get_zones()
        # Geniş bölge: önce dünya, yoksa ilk bölge
        zone = zones.get("world") or zones.get("europe") or list(zones.values())[0]
        bounds = fr_api.get_bounds(zone)
        flights = fr_api.get_flights(bounds=bounds)
        if not flights:
            return None

        # Uçuş numarası mı rota mu? Rota X-Y formatında (örn IST-TZX)
        is_route = "-" in query and len(query) >= 6
        want_origin = want_dest = None
        if is_route:
            parts = query.split("-", 1)
            want_origin, want_dest = parts[0].strip(), parts[1].strip()

        for fr_flight in flights:
            # FlightRadar24 Flight: number, callsign, origin_airport_iata, destination_airport_iata, aircraft_code
            callsign = getattr(fr_flight, "callsign", "") or ""
            number = getattr(fr_flight, "number", "") or ""
            origin_iata = getattr(fr_flight, "origin_airport_iata", None) or ""
            dest_iata = getattr(fr_flight, "destination_airport_iata", None) or ""

            # Eşleşme: uçuş numarası (TK2828 veya 2828) veya rota (IST-TZX)
            if is_route:
                if not want_origin or not want_dest:
                    continue
                if (origin_iata or "").upper() != want_origin or (dest_iata or "").upper() != want_dest:
                    continue
            else:
                # Rakam kısmı veya tam numara (TK2828, THY2828, 2828)
                q_digits = "".join(c for c in query if c.isdigit())
                call_upper = (callsign or str(number)).upper()
                num_str = "".join(c for c in (str(number) + call_upper) if c.isdigit())
                if q_digits and num_str and q_digits not in num_str:
                    continue
                if not q_digits and query not in call_upper and query not in (str(number) or "").upper():
                    continue

            # Detay çek (rota isimleri, koordinatlar, mesafe tahmini için)
            try:
                details = fr_api.get_flight_details(fr_flight)
                if details:
                    fr_flight.set_flight_details(details)
            except Exception:
                pass

            # set_flight_details sonrası: origin_airport_name, destination_airport_name, origin_airport_icao, vb.
            origin_name = getattr(fr_flight, "origin_airport_name", None) or origin_iata or "?"
            dest_name = getattr(fr_flight, "destination_airport_name", None) or dest_iata or "?"
            origin_icao = getattr(fr_flight, "origin_airport_icao", None) or origin_iata
            dest_icao = getattr(fr_flight, "destination_airport_icao", None) or dest_iata
            route_str = f"{origin_iata or origin_icao or '?'}-{dest_iata or dest_icao or '?'}"
            flight_number = (callsign or str(number) or query).strip()

            # Mesafe: önce detaydaki koordinatlardan hesapla, yoksa varsayılan
            distance_km = _distance_from_flight_details(fr_flight)

            # Yolcu: API vermiyor; uçak tipine göre tahmin (aircraft_code: B738, A320 vb.)
            aircraft_type = getattr(fr_flight, "aircraft_code", None)
            expected_passengers = _estimate_passengers_from_aircraft_type(aircraft_type)

            return Flight(
                flight_number=flight_number,
                route=route_str,
                origin=str(origin_name),
                destination=str(dest_name),
                distance_km=round(distance_km, 1),
                expected_passengers=expected_passengers,
            )
        return None
    except Exception:
        return None


# --- Yerel sefer verileri (API yanıt vermediğinde yedek) ---
FLIGHTS: List[Flight] = [
    Flight(flight_number="TK2828", route="IST-TZX", origin="İstanbul", destination="Trabzon", distance_km=900.0, expected_passengers=145),
    Flight(flight_number="TK2424", route="IST-ADB", origin="İstanbul", destination="İzmir", distance_km=325.0, expected_passengers=98),
    Flight(flight_number="TK2162", route="IST-ESB", origin="İstanbul", destination="Ankara", distance_km=350.0, expected_passengers=120),
    Flight(flight_number="TK4002", route="IST-AYT", origin="İstanbul", destination="Antalya", distance_km=475.0, expected_passengers=165),
    Flight(flight_number="TK2840", route="IST-GZT", origin="İstanbul", destination="Gaziantep", distance_km=1050.0, expected_passengers=110),
]

# --- Türk Hava Yolları filo verisi (tek kaynak); id, kapasite, menzil_km, yakit_tuketimi_km ---
ucaklar: List[dict] = [
    # GENİŞ GÖVDE (Kıtalararası - Uzun Menzil)
    {"id": "Airbus A350-900", "kapasite": 329, "menzil_km": 15000, "yakit_tuketimi_km": 5.8},
    {"id": "Boeing 787-9 Dreamliner", "kapasite": 300, "menzil_km": 14140, "yakit_tuketimi_km": 5.4},
    {"id": "Boeing 777-300 ER", "kapasite": 349, "menzil_km": 13600, "yakit_tuketimi_km": 7.5},
    {"id": "Airbus A330-300", "kapasite": 289, "menzil_km": 11750, "yakit_tuketimi_km": 6.2},
    {"id": "Airbus A330-200", "kapasite": 250, "menzil_km": 13450, "yakit_tuketimi_km": 5.9},
    # DAR GÖVDE (Orta/Kısa Menzil)
    {"id": "Airbus A321neo", "kapasite": 190, "menzil_km": 7400, "yakit_tuketimi_km": 2.8},
    {"id": "Airbus A321-200", "kapasite": 180, "menzil_km": 5950, "yakit_tuketimi_km": 3.2},
    {"id": "Airbus A320-200", "kapasite": 153, "menzil_km": 6100, "yakit_tuketimi_km": 3.0},
    {"id": "Airbus A319-100", "kapasite": 132, "menzil_km": 6900, "yakit_tuketimi_km": 2.6},
    {"id": "Boeing 737 MAX 9", "kapasite": 169, "menzil_km": 6500, "yakit_tuketimi_km": 2.7},
    {"id": "Boeing 737-900ER", "kapasite": 151, "menzil_km": 5900, "yakit_tuketimi_km": 3.1},
    {"id": "Boeing 737-800", "kapasite": 165, "menzil_km": 5400, "yakit_tuketimi_km": 3.3},
]


def _manufacturer_from_id(ucak_id: str) -> str:
    """Uçak id'sinden üretici adı (UI ve optimizer uyumu için)."""
    s = (ucak_id or "").upper()
    if "BOEING" in s:
        return "Boeing"
    if "AIRBUS" in s:
        return "Airbus"
    return "Diğer"


def _aircraft_from_ucak(u: dict) -> Aircraft:
    """Sözlük kaydını data.Aircraft nesnesine çevirir."""
    return Aircraft(
        name=u["id"],
        manufacturer=_manufacturer_from_id(u["id"]),
        capacity=u["kapasite"],
        fuel_per_km=u["yakit_tuketimi_km"],
        menzil_km=u["menzil_km"],
    )


# Uygulama tarafında kullanılan Aircraft listesi (ucaklar sözlüğünden türetilir)
AIRCRAFT: List[Aircraft] = [_aircraft_from_ucak(u) for u in ucaklar]


def get_all_flights() -> List[Flight]:
    """Tüm yerel seferleri döndürür."""
    return FLIGHTS.copy()


def get_all_aircraft() -> List[Aircraft]:
    """Tüm uçakları döndürür."""
    return AIRCRAFT.copy()


def find_flight_by_number(flight_number: str) -> Optional[Flight]:
    """Sefer numarasına göre yerel listeden sefer bulur (büyük/küçük harf duyarsız)."""
    key = flight_number.strip().upper()
    for f in FLIGHTS:
        if f.flight_number.upper() == key:
            return f
    return None


def find_flight_by_route(route: str) -> Optional[Flight]:
    """Rota kodu ile yerel listeden sefer bulur (örn: IST-TZX)."""
    key = route.strip().upper().replace(" ", "")
    for f in FLIGHTS:
        if f.route.upper() == key:
            return f
    return None


def find_flight(query: str) -> Optional[Flight]:
    """
    Önce API'den uçuş dener; bulunamazsa veya API yoksa yerel veriden sefer numarası/rota ile arar.
    Arayüz bu fonksiyonu kullanmalı (veri çekme tek noktadan).
    """
    # Önce canlı veri
    flight = fetch_flight_from_api(query)
    if flight is not None:
        return flight
    # Yedek: yerel veri
    return find_flight_by_number(query) or find_flight_by_route(query)
