# -*- coding: utf-8 -*-
"""
AeroZeka — Havayolu filo atama uygulaması.
"""

__version__ = "0.1.0"

from .data import Flight, Aircraft, find_flight_by_number, find_flight_by_route
from .optimization import get_suitable_aircraft, get_ideal_explanation, AircraftCandidate

__all__ = [
    "Flight",
    "Aircraft",
    "AircraftCandidate",
    "find_flight_by_number",
    "find_flight_by_route",
    "get_suitable_aircraft",
    "get_ideal_explanation",
]
