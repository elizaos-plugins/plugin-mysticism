"""Astrology natal chart engine — Python port of typescript/src/engines/astrology/.

Pure-Python natal chart calculator using simplified Keplerian orbital mechanics
referenced to the J2000.0 epoch (January 1, 2000, 12:00 TT).  Accuracy is
typically within 1–2 degrees for inner planets and the Sun, which is sufficient
for zodiac sign determination.

No external dependencies (no Swiss Ephemeris).
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from elizaos_plugin_mysticism.types import (
    AstrologyReadingState,
    BirthData,
    ChartAspect,
    FeedbackEntry,
    NatalChart,
    PlanetPosition,
    SignPosition,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEG2RAD = math.pi / 180.0
RAD2DEG = 180.0 / math.pi
J2000 = 2451545.0  # Julian Day of J2000.0 epoch

# ---------------------------------------------------------------------------
# Sign helpers (port of zodiac.ts)
# ---------------------------------------------------------------------------

SIGN_ORDER: list[str] = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


def degrees_to_sign(total_degrees: float) -> SignPosition:
    """Convert ecliptic longitude to sign + degrees within sign."""
    deg = total_degrees % 360
    if deg < 0:
        deg += 360
    sign_index = int(deg // 30)
    within_sign = deg - sign_index * 30
    return SignPosition(
        sign=SIGN_ORDER[sign_index],
        degrees=within_sign,
        totalDegrees=deg,
    )


# ---------------------------------------------------------------------------
# Aspect definitions (loaded from JSON)
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
_aspect_defs_cache: Optional[list[dict]] = None


def _load_aspect_definitions() -> list[dict]:
    global _aspect_defs_cache
    if _aspect_defs_cache is not None:
        return _aspect_defs_cache
    path = _DATA_DIR / "astrology" / "aspects.json"
    with open(path, "r", encoding="utf-8") as f:
        _aspect_defs_cache = json.load(f)
    return _aspect_defs_cache


# ---------------------------------------------------------------------------
# Orbital elements at J2000.0 (Standish 1992 / Meeus)
# ---------------------------------------------------------------------------

@dataclass
class OrbitalElements:
    L0: float  # Mean longitude at J2000.0 (degrees)
    L1: float  # Mean longitude rate (degrees per Julian century)
    a: float   # Semi-major axis (AU)
    e0: float  # Eccentricity at J2000.0
    e1: float  # Eccentricity rate per century
    I0: float  # Inclination at J2000.0 (degrees)
    I1: float  # Inclination rate per century
    W0: float  # Longitude of ascending node at J2000.0 (degrees)
    W1: float  # Longitude of ascending node rate per century
    w0: float  # Longitude of perihelion at J2000.0 (degrees)
    w1: float  # Longitude of perihelion rate per century


ORBITAL_ELEMENTS: dict[str, OrbitalElements] = {
    "mercury": OrbitalElements(
        L0=252.25032350, L1=149472.67411175,
        a=0.38709927, e0=0.20563593, e1=0.00001906,
        I0=7.00497902, I1=-0.00594749,
        W0=48.33076593, W1=-0.12534081,
        w0=77.45779628, w1=0.16047689,
    ),
    "venus": OrbitalElements(
        L0=181.97909950, L1=58517.81538729,
        a=0.72333566, e0=0.00677672, e1=-0.00004107,
        I0=3.39467605, I1=-0.00078890,
        W0=76.67984255, W1=-0.27769418,
        w0=131.60246718, w1=0.00268329,
    ),
    "earth": OrbitalElements(
        L0=100.46457166, L1=35999.37244981,
        a=1.00000261, e0=0.01671123, e1=-0.00004392,
        I0=0.00001531, I1=-0.01294668,
        W0=0.0, W1=0.0,
        w0=102.93768193, w1=0.32327364,
    ),
    "mars": OrbitalElements(
        L0=355.44656299, L1=19140.30268499,
        a=1.52371034, e0=0.09339410, e1=0.00007882,
        I0=1.84969142, I1=-0.00813131,
        W0=49.55953891, W1=-0.29257343,
        w0=336.05637041, w1=0.44441088,
    ),
    "jupiter": OrbitalElements(
        L0=34.39644051, L1=3034.74612775,
        a=5.20288700, e0=0.04838624, e1=-0.00013253,
        I0=1.30439695, I1=-0.00183714,
        W0=100.47390909, W1=0.20469106,
        w0=14.72847983, w1=0.21252668,
    ),
    "saturn": OrbitalElements(
        L0=49.95424423, L1=1222.49362201,
        a=9.53667594, e0=0.05386179, e1=-0.00050991,
        I0=2.48599187, I1=0.00193609,
        W0=113.66242448, W1=-0.28867794,
        w0=92.59887831, w1=-0.41897216,
    ),
    "uranus": OrbitalElements(
        L0=313.23810451, L1=428.48202785,
        a=19.18916464, e0=0.04725744, e1=-0.00004397,
        I0=0.77263783, I1=-0.00242939,
        W0=74.01692503, W1=0.04240589,
        w0=170.95427630, w1=0.40805281,
    ),
    "neptune": OrbitalElements(
        L0=304.87997031, L1=218.45945325,
        a=30.06992276, e0=0.00859048, e1=0.00005105,
        I0=1.77004347, I1=0.00035372,
        W0=131.78422574, W1=-0.01299630,
        w0=44.96476227, w1=-0.32241464,
    ),
    "pluto": OrbitalElements(
        L0=238.92903833, L1=145.20780515,
        a=39.48211675, e0=0.24882730, e1=0.00005170,
        I0=17.14001206, I1=0.00004818,
        W0=110.30393684, W1=-0.01183482,
        w0=224.06891629, w1=-0.04062942,
    ),
}


# ---------------------------------------------------------------------------
# Julian Day calculation
# ---------------------------------------------------------------------------


def to_julian_day(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
) -> float:
    """Convert a calendar date + time to Julian Day Number.

    Handles both Julian and Gregorian calendars.
    """
    y = year
    m = month
    if m <= 2:
        y -= 1
        m += 12
    A = y // 100
    B = 2 - A + A // 4
    day_fraction = (hour + minute / 60) / 24
    return (
        int(365.25 * (y + 4716))
        + int(30.6001 * (m + 1))
        + day
        + day_fraction
        + B
        - 1524.5
    )


def julian_centuries(jd: float) -> float:
    """Julian centuries since J2000.0."""
    return (jd - J2000) / 36525.0


# ---------------------------------------------------------------------------
# Angle normalisation
# ---------------------------------------------------------------------------


def _norm_deg(deg: float) -> float:
    """Normalise angle to [0, 360)."""
    return deg % 360 if deg >= 0 else (deg % 360 + 360) % 360


# ---------------------------------------------------------------------------
# Kepler's equation solver (Newton-Raphson)
# ---------------------------------------------------------------------------


def solve_kepler(M: float, e: float) -> float:
    """Solve Kepler's equation M = E - e*sin(E) for E (eccentric anomaly).

    M and E in radians.
    """
    E = M  # initial guess
    for _ in range(50):
        dE = (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
        E -= dE
        if abs(dE) < 1e-12:
            break
    return E


# ---------------------------------------------------------------------------
# Heliocentric ecliptic longitude
# ---------------------------------------------------------------------------


def heliocentric_longitude(planet_id: str, jd: float) -> float:
    """Compute heliocentric ecliptic longitude for a planet at a given JD."""
    el = ORBITAL_ELEMENTS.get(planet_id)
    if el is None:
        raise ValueError(f"No orbital elements for: {planet_id}")

    T = julian_centuries(jd)

    # Current elements
    L = _norm_deg(el.L0 + el.L1 * T)
    e = el.e0 + el.e1 * T
    w = _norm_deg(el.w0 + el.w1 * T)
    W = _norm_deg(el.W0 + el.W1 * T)
    I = el.I0 + el.I1 * T

    # Mean anomaly
    M = _norm_deg(L - w)
    M_rad = M * DEG2RAD

    # Solve Kepler's equation
    E = solve_kepler(M_rad, e)

    # True anomaly
    sin_v = (math.sqrt(1 - e * e) * math.sin(E)) / (1 - e * math.cos(E))
    cos_v = (math.cos(E) - e) / (1 - e * math.cos(E))
    v = math.atan2(sin_v, cos_v) * RAD2DEG

    # Heliocentric longitude in the orbital plane
    l_helio = _norm_deg(v + w - W)

    # Convert from orbital plane to ecliptic
    I_rad = I * DEG2RAD
    l_helio_rad = l_helio * DEG2RAD

    ecl_lon = _norm_deg(
        math.atan2(
            math.sin(l_helio_rad) * math.cos(I_rad),
            math.cos(l_helio_rad),
        ) * RAD2DEG + W
    )

    return ecl_lon


# ---------------------------------------------------------------------------
# Geocentric ecliptic longitude
# ---------------------------------------------------------------------------


def geocentric_longitude(planet_id: str, jd: float) -> float:
    """Convert heliocentric position to geocentric (as seen from Earth)."""
    if planet_id == "earth":
        raise ValueError("Cannot compute geocentric longitude of Earth")

    T = julian_centuries(jd)

    # Earth's heliocentric position
    earth_el = ORBITAL_ELEMENTS["earth"]
    earth_L = _norm_deg(earth_el.L0 + earth_el.L1 * T)
    earth_e = earth_el.e0 + earth_el.e1 * T
    earth_w = _norm_deg(earth_el.w0 + earth_el.w1 * T)
    earth_M = _norm_deg(earth_L - earth_w) * DEG2RAD
    earth_ecc = solve_kepler(earth_M, earth_e)
    earth_V = (
        math.atan2(
            math.sqrt(1 - earth_e * earth_e) * math.sin(earth_ecc),
            math.cos(earth_ecc) - earth_e,
        )
        * RAD2DEG
    )
    earth_helio_lon = _norm_deg(earth_V + earth_w)
    earth_R = earth_el.a * (1 - earth_e * math.cos(earth_ecc))

    # Planet's heliocentric position
    p_el = ORBITAL_ELEMENTS[planet_id]
    p_L = _norm_deg(p_el.L0 + p_el.L1 * T)
    p_e = p_el.e0 + p_el.e1 * T
    p_w = _norm_deg(p_el.w0 + p_el.w1 * T)
    p_M = _norm_deg(p_L - p_w) * DEG2RAD
    p_ecc = solve_kepler(p_M, p_e)
    p_V = (
        math.atan2(
            math.sqrt(1 - p_e * p_e) * math.sin(p_ecc),
            math.cos(p_ecc) - p_e,
        )
        * RAD2DEG
    )
    p_helio_lon = _norm_deg(p_V + p_w)
    p_R = p_el.a * (1 - p_e * math.cos(p_ecc))

    # Convert to geocentric using simple 2D projection (ecliptic plane)
    p_helio_rad = p_helio_lon * DEG2RAD
    earth_helio_rad = earth_helio_lon * DEG2RAD

    x = p_R * math.cos(p_helio_rad) - earth_R * math.cos(earth_helio_rad)
    y = p_R * math.sin(p_helio_rad) - earth_R * math.sin(earth_helio_rad)

    return _norm_deg(math.atan2(y, x) * RAD2DEG)


# ---------------------------------------------------------------------------
# Sun longitude (geocentric)
# ---------------------------------------------------------------------------


def sun_longitude(jd: float) -> float:
    """Compute the Sun's geocentric ecliptic longitude.

    Uses the equation of center (Meeus).
    """
    T = julian_centuries(jd)

    # Sun's mean longitude
    L0 = _norm_deg(280.46646 + 36000.76983 * T + 0.0003032 * T * T)

    # Sun's mean anomaly
    M = _norm_deg(357.52911 + 35999.05029 * T - 0.0001537 * T * T)
    M_rad = M * DEG2RAD

    # Equation of center
    C = (
        (1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M_rad)
        + (0.019993 - 0.000101 * T) * math.sin(2 * M_rad)
        + 0.000289 * math.sin(3 * M_rad)
    )

    # Sun's true longitude
    sun_true_lon = _norm_deg(L0 + C)

    # Apparent longitude (nutation and aberration correction)
    omega = 125.04 - 1934.136 * T
    apparent = sun_true_lon - 0.00569 - 0.00478 * math.sin(omega * DEG2RAD)

    return _norm_deg(apparent)


# ---------------------------------------------------------------------------
# Moon longitude (Meeus 24-term lunar theory)
# ---------------------------------------------------------------------------


def moon_longitude(jd: float) -> float:
    """Compute the Moon's geocentric ecliptic longitude.

    Uses the principal terms of the lunar theory (Meeus Chapter 47).
    """
    T = julian_centuries(jd)

    # Moon's mean longitude
    Lp = _norm_deg(
        218.3164477
        + 481267.88123421 * T
        - 0.0015786 * T * T
        + T * T * T / 538841
        - T * T * T * T / 65194000
    )

    # Moon's mean elongation
    D = _norm_deg(
        297.8501921
        + 445267.1114034 * T
        - 0.0018819 * T * T
        + T * T * T / 545868
        - T * T * T * T / 113065000
    )

    # Sun's mean anomaly
    M = _norm_deg(
        357.5291092
        + 35999.0502909 * T
        - 0.0001536 * T * T
        + T * T * T / 24490000
    )

    # Moon's mean anomaly
    Mp = _norm_deg(
        134.9633964
        + 477198.8675055 * T
        + 0.0087414 * T * T
        + T * T * T / 69699
        - T * T * T * T / 14712000
    )

    # Moon's argument of latitude
    F = _norm_deg(
        93.2720950
        + 483202.0175233 * T
        - 0.0036539 * T * T
        - T * T * T / 3526000
        + T * T * T * T / 863310000
    )

    D_rad = D * DEG2RAD
    M_rad = M * DEG2RAD
    Mp_rad = Mp * DEG2RAD
    F_rad = F * DEG2RAD

    # Principal terms for longitude (simplified from Meeus Table 47.A)
    sum_L = 0.0
    sum_L += 6288774 * math.sin(Mp_rad)
    sum_L += 1274027 * math.sin(2 * D_rad - Mp_rad)
    sum_L += 658314 * math.sin(2 * D_rad)
    sum_L += 213618 * math.sin(2 * Mp_rad)
    sum_L += -185116 * math.sin(M_rad)
    sum_L += -114332 * math.sin(2 * F_rad)
    sum_L += 58793 * math.sin(2 * D_rad - 2 * Mp_rad)
    sum_L += 57066 * math.sin(2 * D_rad - M_rad - Mp_rad)
    sum_L += 53322 * math.sin(2 * D_rad + Mp_rad)
    sum_L += 45758 * math.sin(2 * D_rad - M_rad)
    sum_L += -40923 * math.sin(M_rad - Mp_rad)
    sum_L += -34720 * math.sin(D_rad)
    sum_L += -30383 * math.sin(M_rad + Mp_rad)
    sum_L += 15327 * math.sin(2 * D_rad - 2 * F_rad)
    sum_L += -12528 * math.sin(Mp_rad + 2 * F_rad)
    sum_L += 10980 * math.sin(Mp_rad - 2 * F_rad)
    sum_L += 10675 * math.sin(4 * D_rad - Mp_rad)
    sum_L += 10034 * math.sin(3 * Mp_rad)
    sum_L += 8548 * math.sin(4 * D_rad - 2 * Mp_rad)
    sum_L += -7888 * math.sin(2 * D_rad + M_rad - Mp_rad)
    sum_L += -6766 * math.sin(2 * D_rad + M_rad)
    sum_L += -5163 * math.sin(D_rad - Mp_rad)
    sum_L += 4987 * math.sin(D_rad + M_rad)
    sum_L += 4036 * math.sin(2 * D_rad - M_rad + Mp_rad)

    # Convert from 0.000001 degrees to degrees
    moon_lon = _norm_deg(Lp + sum_L / 1_000_000)

    return moon_lon


# ---------------------------------------------------------------------------
# Retrograde detection
# ---------------------------------------------------------------------------


def _is_retrograde(planet_id: str, jd: float) -> bool:
    """Determine if a planet appears retrograde by comparing longitude ±1 day."""
    if planet_id in ("sun", "moon"):
        return False

    lon_before = geocentric_longitude(planet_id, jd - 1)
    lon_after = geocentric_longitude(planet_id, jd + 1)

    # Handle wrapping around 0/360 degrees
    diff = lon_after - lon_before
    if diff > 180:
        diff -= 360
    if diff < -180:
        diff += 360

    return diff < 0


# ---------------------------------------------------------------------------
# Obliquity of the ecliptic
# ---------------------------------------------------------------------------


def _obliquity(jd: float) -> float:
    """Mean obliquity of the ecliptic (Laskar formula)."""
    T = julian_centuries(jd)
    return (
        23.4392911
        - 0.0130042 * T
        - 1.64e-7 * T * T
        + 5.036e-7 * T * T * T
    )


# ---------------------------------------------------------------------------
# Ascendant & Midheaven (MC)
# ---------------------------------------------------------------------------


def _local_sidereal_time(jd: float, lon_deg: float) -> float:
    """Compute Local Sidereal Time in degrees."""
    T = julian_centuries(jd)
    # Greenwich Mean Sidereal Time in degrees
    gmst = _norm_deg(
        280.46061837
        + 360.98564736629 * (jd - J2000)
        + 0.000387933 * T * T
        - T * T * T / 38710000
    )
    return _norm_deg(gmst + lon_deg)


def compute_ascendant(lst_deg: float, lat_deg: float, obl_deg: float) -> float:
    """Calculate the Ascendant (rising sign) from LST, latitude, and obliquity."""
    lst_rad = lst_deg * DEG2RAD
    lat_rad = lat_deg * DEG2RAD
    obl_rad = obl_deg * DEG2RAD

    y = -math.cos(lst_rad)
    x = math.sin(obl_rad) * math.tan(lat_rad) + math.cos(obl_rad) * math.sin(lst_rad)

    asc = math.atan2(y, x) * RAD2DEG
    return _norm_deg(asc)


def compute_midheaven(lst_deg: float, obl_deg: float) -> float:
    """Calculate the Midheaven (Medium Coeli) from LST and obliquity."""
    lst_rad = lst_deg * DEG2RAD
    obl_rad = obl_deg * DEG2RAD

    mc = math.atan2(
        math.sin(lst_rad),
        math.cos(lst_rad) * math.cos(obl_rad),
    ) * RAD2DEG
    return _norm_deg(mc)


# ---------------------------------------------------------------------------
# House cusps (Equal house system)
# ---------------------------------------------------------------------------


def _equal_house_cusps(asc_deg: float) -> list[float]:
    """Calculate equal house cusps from the Ascendant (each house = 30 deg)."""
    return [_norm_deg(asc_deg + i * 30) for i in range(12)]


def _house_for_longitude(longitude: float, cusps: list[float]) -> int:
    """Determine which house (1-12) a planet falls in."""
    for i in range(12):
        cusp = cusps[i]
        next_cusp = cusps[(i + 1) % 12]

        if next_cusp > cusp:
            # Normal case: cusp doesn't wrap around 360
            if cusp <= longitude < next_cusp:
                return i + 1
        else:
            # Wraps around 0 degrees
            if longitude >= cusp or longitude < next_cusp:
                return i + 1
    return 1  # fallback


# ---------------------------------------------------------------------------
# Sun sign from date (calendar-based, traditional boundaries)
# ---------------------------------------------------------------------------

_SUN_SIGN_DATES: list[dict[str, object]] = [
    {"sign": "capricorn",   "startMonth": 1,  "startDay": 1},
    {"sign": "aquarius",    "startMonth": 1,  "startDay": 20},
    {"sign": "pisces",      "startMonth": 2,  "startDay": 19},
    {"sign": "aries",       "startMonth": 3,  "startDay": 21},
    {"sign": "taurus",      "startMonth": 4,  "startDay": 20},
    {"sign": "gemini",      "startMonth": 5,  "startDay": 21},
    {"sign": "cancer",      "startMonth": 6,  "startDay": 21},
    {"sign": "leo",         "startMonth": 7,  "startDay": 23},
    {"sign": "virgo",       "startMonth": 8,  "startDay": 23},
    {"sign": "libra",       "startMonth": 9,  "startDay": 23},
    {"sign": "scorpio",     "startMonth": 10, "startDay": 23},
    {"sign": "sagittarius", "startMonth": 11, "startDay": 22},
    {"sign": "capricorn",   "startMonth": 12, "startDay": 22},
]


def calculate_sun_sign(month: int, day: int) -> str:
    """Determine the Sun sign from month and day using traditional boundaries."""
    for boundary in reversed(_SUN_SIGN_DATES):
        start_month = boundary["startMonth"]
        start_day = boundary["startDay"]
        assert isinstance(start_month, int) and isinstance(start_day, int)
        if month > start_month or (month == start_month and day >= start_day):
            return str(boundary["sign"])
    return "capricorn"


# ---------------------------------------------------------------------------
# Aspect calculation
# ---------------------------------------------------------------------------


def calculate_aspects(positions: list[PlanetPosition]) -> list[ChartAspect]:
    """Calculate all aspects between planet positions."""
    aspects: list[ChartAspect] = []
    definitions = _load_aspect_definitions()

    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            p1 = positions[i]
            p2 = positions[j]

            separation = abs(p1.totalDegrees - p2.totalDegrees)
            if separation > 180:
                separation = 360 - separation

            for defn in definitions:
                orb_distance = abs(separation - defn["degrees"])
                if orb_distance <= defn["orb"]:
                    aspects.append(
                        ChartAspect(
                            planet1=p1.planet,
                            planet2=p2.planet,
                            aspectName=defn["name"],
                            aspectSymbol=defn["symbol"],
                            exactDegrees=defn["degrees"],
                            actualDegrees=separation,
                            orb=round(orb_distance * 100) / 100,
                            nature=defn["nature"],
                        )
                    )

    # Sort by tightest orb first
    aspects.sort(key=lambda a: a.orb)
    return aspects


# ---------------------------------------------------------------------------
# Build a PlanetPosition
# ---------------------------------------------------------------------------


def _build_position(
    planet_name: str,
    longitude: float,
    house_cusps: list[float],
    retrograde: bool,
) -> PlanetPosition:
    sign_pos = degrees_to_sign(longitude)
    return PlanetPosition(
        planet=planet_name,
        sign=sign_pos.sign,
        degrees=round(sign_pos.degrees * 100) / 100,
        totalDegrees=round(sign_pos.totalDegrees * 100) / 100,
        house=_house_for_longitude(longitude, house_cusps),
        retrograde=retrograde,
    )


# ---------------------------------------------------------------------------
# Main chart calculation
# ---------------------------------------------------------------------------


def calculate_natal_chart(birth_data: BirthData) -> NatalChart:
    """Calculate a complete natal chart from birth data.

    For BirthData with null fields: default hour to 12, minute to 0,
    lat/lon to 0/0, timezone to 0 (same as TypeScript service does).
    """
    # Apply defaults for nullable fields
    day = birth_data.day if birth_data.day is not None else 1
    hour = birth_data.hour if birth_data.hour is not None else 12
    minute = birth_data.minute if birth_data.minute is not None else 0
    latitude = birth_data.latitude if birth_data.latitude is not None else 0.0
    longitude_geo = birth_data.longitude if birth_data.longitude is not None else 0.0
    timezone = birth_data.timezone if birth_data.timezone is not None else 0.0

    # Convert birth time to UT
    ut_hour = hour - timezone
    ut_minute = minute

    # Calculate Julian Day
    jd = to_julian_day(birth_data.year, birth_data.month, day, ut_hour, ut_minute)

    # Obliquity of the ecliptic
    obl = _obliquity(jd)

    # Local Sidereal Time
    lst = _local_sidereal_time(jd, longitude_geo)

    # Ascendant and Midheaven
    asc_deg = compute_ascendant(lst, latitude, obl)
    mc_deg = compute_midheaven(lst, obl)

    # House cusps (equal house system)
    cusps = _equal_house_cusps(asc_deg)

    # Compute planetary positions
    sun_lon = sun_longitude(jd)
    moon_lon = moon_longitude(jd)
    mercury_lon = geocentric_longitude("mercury", jd)
    venus_lon = geocentric_longitude("venus", jd)
    mars_lon = geocentric_longitude("mars", jd)
    jupiter_lon = geocentric_longitude("jupiter", jd)
    saturn_lon = geocentric_longitude("saturn", jd)
    uranus_lon = geocentric_longitude("uranus", jd)
    neptune_lon = geocentric_longitude("neptune", jd)
    pluto_lon = geocentric_longitude("pluto", jd)

    # Build planet positions
    sun = _build_position("sun", sun_lon, cusps, False)
    moon = _build_position("moon", moon_lon, cusps, False)
    mercury = _build_position("mercury", mercury_lon, cusps, _is_retrograde("mercury", jd))
    venus = _build_position("venus", venus_lon, cusps, _is_retrograde("venus", jd))
    mars = _build_position("mars", mars_lon, cusps, _is_retrograde("mars", jd))
    jupiter = _build_position("jupiter", jupiter_lon, cusps, _is_retrograde("jupiter", jd))
    saturn = _build_position("saturn", saturn_lon, cusps, _is_retrograde("saturn", jd))
    uranus = _build_position("uranus", uranus_lon, cusps, _is_retrograde("uranus", jd))
    neptune = _build_position("neptune", neptune_lon, cusps, _is_retrograde("neptune", jd))
    pluto = _build_position("pluto", pluto_lon, cusps, _is_retrograde("pluto", jd))

    # Ascendant and Midheaven as SignPositions
    ascendant = degrees_to_sign(asc_deg)
    midheaven = degrees_to_sign(mc_deg)

    # Calculate aspects between all planets
    all_positions = [sun, moon, mercury, venus, mars, jupiter, saturn, uranus, neptune, pluto]
    aspects = calculate_aspects(all_positions)

    return NatalChart(
        sun=sun,
        moon=moon,
        mercury=mercury,
        venus=venus,
        mars=mars,
        jupiter=jupiter,
        saturn=saturn,
        uranus=uranus,
        neptune=neptune,
        pluto=pluto,
        ascendant=ascendant,
        midheaven=midheaven,
        aspects=aspects,
        houseCusps=cusps,
    )


# ---------------------------------------------------------------------------
# Default reveal order
# ---------------------------------------------------------------------------

DEFAULT_REVEAL_ORDER: list[str] = [
    "sun", "moon", "ascendant", "mercury", "venus", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
]


# ---------------------------------------------------------------------------
# AstrologyEngine
# ---------------------------------------------------------------------------


class AstrologyEngine:
    """Stateless astrology engine — all reading state lives in AstrologyReadingState."""

    def start_reading(self, birth_data: BirthData) -> AstrologyReadingState:
        chart = calculate_natal_chart(birth_data)
        return AstrologyReadingState(
            birthData=birth_data,
            chart=chart,
            revealedPlanets=[],
            revealedHouses=[],
            userFeedback=[],
        )

    def get_next_reveal(
        self,
        state: AstrologyReadingState,
    ) -> Optional[dict]:
        """Return the next planet to reveal, or None when done."""
        revealed = set(state.revealedPlanets)
        for planet_id in DEFAULT_REVEAL_ORDER:
            if planet_id not in revealed:
                position = self._get_chart_position(planet_id, state.chart)
                return {"planet": planet_id, "position": position}
        return None

    def record_feedback(
        self,
        state: AstrologyReadingState,
        planet_id: str,
        feedback: FeedbackEntry,
    ) -> AstrologyReadingState:
        return AstrologyReadingState(
            birthData=state.birthData,
            chart=state.chart,
            revealedPlanets=[*state.revealedPlanets, planet_id],
            revealedHouses=list(state.revealedHouses),
            userFeedback=[*state.userFeedback, feedback],
        )

    def get_synthesis(self, state: AstrologyReadingState) -> dict:
        """Return a summary of the reading."""
        chart = state.chart
        return {
            "sunSign": chart.sun.sign,
            "moonSign": chart.moon.sign,
            "ascendant": chart.ascendant.sign,
            "planets": {
                p.planet: {"sign": p.sign, "degrees": p.degrees, "house": p.house}
                for p in [
                    chart.sun, chart.moon, chart.mercury, chart.venus, chart.mars,
                    chart.jupiter, chart.saturn, chart.uranus, chart.neptune, chart.pluto,
                ]
            },
            "aspects": [
                {
                    "planet1": a.planet1,
                    "planet2": a.planet2,
                    "aspectName": a.aspectName,
                    "orb": a.orb,
                }
                for a in chart.aspects
            ],
        }

    def get_sun_sign(self, month: int, day: int) -> str:
        return calculate_sun_sign(month, day)

    def compute_chart(self, birth_data: BirthData) -> NatalChart:
        return calculate_natal_chart(birth_data)

    def is_complete(self, state: AstrologyReadingState) -> bool:
        return len(state.revealedPlanets) >= len(DEFAULT_REVEAL_ORDER)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_chart_position(
        planet_id: str,
        chart: NatalChart,
    ) -> Optional[PlanetPosition | SignPosition]:
        """Get a planet or point position from the chart."""
        if planet_id == "ascendant":
            return PlanetPosition(
                planet="ascendant",
                sign=chart.ascendant.sign,
                degrees=chart.ascendant.degrees,
                totalDegrees=chart.ascendant.totalDegrees,
                house=1,
                retrograde=False,
            )
        if planet_id == "midheaven":
            return PlanetPosition(
                planet="midheaven",
                sign=chart.midheaven.sign,
                degrees=chart.midheaven.degrees,
                totalDegrees=chart.midheaven.totalDegrees,
                house=10,
                retrograde=False,
            )
        return getattr(chart, planet_id, None)
