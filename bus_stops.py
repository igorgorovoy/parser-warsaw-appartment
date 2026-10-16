#!/usr/bin/env python3
"""
School bus stops (Nova Study, Piaseczno, 2026-2027) and distance helpers.
Coordinates come from Warsaw ZTM GTFS (stops.txt, https://mkuran.pl/gtfs/warsaw.zip).
"""

import math
from typing import Optional, Tuple

# (route, stop name with ZTM code, latitude, longitude)
BUS_STOPS = [
    # Wilanow
    ('Wilanow', 'Sadyba 01', 52.181762, 21.068999),
    ('Wilanow', 'Sadyba 02', 52.182764, 21.068458),
    ('Wilanow', 'Łowcza 01', 52.174364, 21.078300),
    ('Wilanow', 'Królowej Marysieńki 01', 52.167715, 21.076545),
    ('Wilanow', 'Kosiarzy 02', 52.172268, 21.080955),
    ('Wilanow', 'Miasteczko Wilanów 04', 52.156476, 21.075679),
    ('Wilanow', 'Miasteczko Wilanów 03', 52.157075, 21.078269),
    ('Wilanow', 'Płaskowickiej 04', 52.148834, 21.058577),
    ('Wilanow', 'Płaskowickiej 03', 52.149660, 21.060775),
    ('Wilanow', 'Natolin Płn. 22', 52.144619, 21.049996),
    ('Wilanow', 'Braci Wagów 01', 52.144275, 21.049540),
    ('Wilanow', 'Pileckiego 02', 52.140811, 21.037492),
    ('Wilanow', 'Indiry Gandhi 01', 52.141513, 21.033170),
    # Arcadia
    ('Arcadia', 'Metro Młociny 01', 52.289887, 20.931206),
    ('Arcadia', 'Baseny Inflancka 02', 52.256285, 20.986321),
    ('Arcadia', 'Baseny Inflancka 01', 52.256513, 20.988280),
    ('Arcadia', 'Cmentarz Żydowski 01', 52.244723, 20.976977),
    ('Arcadia', 'Cmentarz Żydowski 02', 52.244819, 20.977509),
    ('Arcadia', 'Metro Świętokrzyska 04', 52.235027, 21.007284),
    ('Arcadia', 'Rondo ONZ 01', 52.231710, 20.998998),
    ('Arcadia', 'Rondo ONZ 02', 52.234479, 20.997964),
    ('Arcadia', 'Rondo Unii Europejskiej 06', 52.179055, 21.002602),
    ('Arcadia', 'Domaniewska 01', 52.182702, 21.001947),
    ('Arcadia', 'Bokserska 01', 52.169394, 20.996422),
    ('Arcadia', 'Bokserska 03', 52.169382, 20.998217),
    ('Arcadia', 'Jurajska 01', 52.162390, 20.992240),
    # Mokotow
    ('Mokotow', 'Dominikańska 02', 52.177359, 21.033608),
    ('Mokotow', 'Piaseczno PKP 01', 52.065282, 21.019095),
    ('Mokotow', 'Piaseczno PKP 02', 52.065929, 21.020273),
]


def distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line (haversine) distance in meters"""
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_stop(lat: float, lon: float) -> Optional[Tuple[str, str, int]]:
    """Return (route, stop, meters) of the closest school bus stop"""
    if lat is None or lon is None:
        return None
    route, stop, slat, slon = min(BUS_STOPS, key=lambda s: distance_m(lat, lon, s[2], s[3]))
    return route, stop, round(distance_m(lat, lon, slat, slon))
