"""Smoke tests for the Astrology engine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elizaos_plugin_mysticism.engines.astrology import (
    AstrologyEngine,
    calculate_aspects,
    calculate_natal_chart,
    calculate_sun_sign,
    compute_ascendant,
    compute_midheaven,
    degrees_to_sign,
    geocentric_longitude,
    moon_longitude,
    solve_kepler,
    sun_longitude,
    to_julian_day,
)
from elizaos_plugin_mysticism.types import BirthData, FeedbackEntry


# ------------------------------------------------------------------
# Sun sign calculation
# ------------------------------------------------------------------


def test_sun_sign_aries():
    assert calculate_sun_sign(3, 25) == "aries"


def test_sun_sign_taurus():
    assert calculate_sun_sign(4, 25) == "taurus"


def test_sun_sign_cancer():
    assert calculate_sun_sign(7, 4) == "cancer"


def test_sun_sign_capricorn_december():
    assert calculate_sun_sign(12, 25) == "capricorn"


def test_sun_sign_capricorn_january():
    assert calculate_sun_sign(1, 5) == "capricorn"


def test_sun_sign_aquarius():
    assert calculate_sun_sign(1, 25) == "aquarius"


def test_sun_sign_pisces():
    assert calculate_sun_sign(3, 10) == "pisces"


def test_sun_sign_leo():
    assert calculate_sun_sign(8, 10) == "leo"


# ------------------------------------------------------------------
# Julian Day calculation
# ------------------------------------------------------------------


def test_julian_day_j2000():
    # J2000.0 = January 1, 2000 at 12:00 TT → JD 2451545.0
    jd = to_julian_day(2000, 1, 1, 12, 0)
    assert abs(jd - 2451545.0) < 0.001


def test_julian_day_known():
    # April 10, 1990 at 0h → JD 2447991.5
    jd = to_julian_day(1990, 4, 10, 0, 0)
    assert abs(jd - 2447991.5) < 0.001


# ------------------------------------------------------------------
# Kepler equation solver
# ------------------------------------------------------------------


def test_kepler_circular():
    import math
    # For circular orbit (e=0), E should equal M
    M = 1.0  # radians
    E = solve_kepler(M, 0.0)
    assert abs(E - M) < 1e-10


def test_kepler_eccentric():
    import math
    # For e=0.5, M=1.0, solve and verify M = E - e*sin(E)
    M = 1.0
    e = 0.5
    E = solve_kepler(M, e)
    computed_M = E - e * math.sin(E)
    assert abs(computed_M - M) < 1e-10


# ------------------------------------------------------------------
# Degrees to sign
# ------------------------------------------------------------------


def test_degrees_to_sign_aries():
    pos = degrees_to_sign(15.0)
    assert pos.sign == "aries"
    assert abs(pos.degrees - 15.0) < 0.01


def test_degrees_to_sign_taurus():
    pos = degrees_to_sign(45.0)
    assert pos.sign == "taurus"
    assert abs(pos.degrees - 15.0) < 0.01


def test_degrees_to_sign_pisces():
    pos = degrees_to_sign(350.0)
    assert pos.sign == "pisces"
    assert abs(pos.degrees - 20.0) < 0.01


def test_degrees_to_sign_wrap():
    pos = degrees_to_sign(370.0)
    assert pos.sign == "aries"
    assert abs(pos.degrees - 10.0) < 0.01


# ------------------------------------------------------------------
# Natal chart calculation
# ------------------------------------------------------------------


def test_known_date_sun_sign():
    """A person born March 25, 1990 should have Sun in Aries."""
    birth = BirthData(year=1990, month=3, day=25, hour=12, minute=0,
                      latitude=40.7128, longitude=-74.0060, timezone=-5)
    chart = calculate_natal_chart(birth)
    assert chart.sun.sign == "aries"


def test_chart_has_all_planets():
    birth = BirthData(year=1985, month=6, day=15, hour=10, minute=30,
                      latitude=51.5074, longitude=-0.1278, timezone=0)
    chart = calculate_natal_chart(birth)

    # All planet positions must be populated
    planet_names = ["sun", "moon", "mercury", "venus", "mars",
                    "jupiter", "saturn", "uranus", "neptune", "pluto"]
    for name in planet_names:
        pos = getattr(chart, name)
        assert pos is not None
        assert pos.planet == name
        assert 0 <= pos.totalDegrees < 360
        assert 1 <= pos.house <= 12

    # Ascendant and midheaven
    assert chart.ascendant.sign in [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    ]
    assert chart.midheaven.sign in [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    ]

    # House cusps
    assert len(chart.houseCusps) == 12


def test_chart_with_null_fields():
    """BirthData with None fields should use defaults."""
    birth = BirthData(year=2000, month=6)
    chart = calculate_natal_chart(birth)
    assert chart.sun.sign in [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    ]


def test_aspects_populated():
    birth = BirthData(year=1990, month=3, day=25, hour=12, minute=0,
                      latitude=40.7128, longitude=-74.0060, timezone=-5)
    chart = calculate_natal_chart(birth)
    # There should be at least some aspects
    assert len(chart.aspects) > 0
    for a in chart.aspects:
        assert a.orb >= 0


def test_cancer_sun_sign():
    """July 4, 1776 should produce a Cancer sun."""
    birth = BirthData(year=1776, month=7, day=4, hour=12, minute=0,
                      latitude=39.9526, longitude=-75.1652, timezone=-5)
    chart = calculate_natal_chart(birth)
    assert chart.sun.sign == "cancer"


# ------------------------------------------------------------------
# Engine lifecycle
# ------------------------------------------------------------------


def test_engine_start_reading():
    engine = AstrologyEngine()
    birth = BirthData(year=1990, month=3, day=25, hour=12, minute=0,
                      latitude=40.7128, longitude=-74.0060, timezone=-5)
    state = engine.start_reading(birth)
    assert state.chart is not None
    assert len(state.revealedPlanets) == 0


def test_engine_reveal_cycle():
    engine = AstrologyEngine()
    birth = BirthData(year=1990, month=3, day=25, hour=12, minute=0,
                      latitude=40.7128, longitude=-74.0060, timezone=-5)
    state = engine.start_reading(birth)

    count = 0
    while True:
        reveal = engine.get_next_reveal(state)
        if reveal is None:
            break
        planet_id = reveal["planet"]
        feedback = FeedbackEntry(element=planet_id, userText="Understood", timestamp=0)
        state = engine.record_feedback(state, planet_id, feedback)
        count += 1

    assert engine.is_complete(state)
    assert count == 11  # sun, moon, ascendant, + 8 planets


def test_engine_synthesis():
    engine = AstrologyEngine()
    birth = BirthData(year=1990, month=3, day=25, hour=12, minute=0,
                      latitude=40.7128, longitude=-74.0060, timezone=-5)
    state = engine.start_reading(birth)

    synthesis = engine.get_synthesis(state)
    assert "sunSign" in synthesis
    assert "moonSign" in synthesis
    assert "ascendant" in synthesis
    assert "planets" in synthesis


def test_engine_sun_sign_shortcut():
    engine = AstrologyEngine()
    assert engine.get_sun_sign(7, 4) == "cancer"
    assert engine.get_sun_sign(12, 25) == "capricorn"
