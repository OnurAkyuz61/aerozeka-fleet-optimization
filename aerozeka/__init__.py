# -*- coding: utf-8 -*-
"""
AeroZeka — Havayolu filo atama uygulaması.
"""

__version__ = "0.1.0"

from .data import (
    Flight,
    Aircraft,
    find_flight,
    find_flight_by_number,
    find_flight_by_route,
    fetch_flight_from_api,
)
from .optimization import get_suitable_aircraft, get_ideal_explanation, AircraftCandidate

__all__ = [
    "Flight",
    "Aircraft",
    "AircraftCandidate",
    "find_flight",
    "find_flight_by_number",
    "find_flight_by_route",
    "fetch_flight_from_api",
    "get_suitable_aircraft",
    "get_ideal_explanation",
]
