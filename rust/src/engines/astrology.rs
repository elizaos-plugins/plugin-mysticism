use crate::types::{BirthData, ChartAspect, NatalChart, PlanetPosition, SignPosition};

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DEG2RAD: f64 = std::f64::consts::PI / 180.0;
const RAD2DEG: f64 = 180.0 / std::f64::consts::PI;
const J2000: f64 = 2_451_545.0; // Julian Day of J2000.0 epoch

/// Sign order (tropical zodiac).
const SIGN_ORDER: [&str; 12] = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
];

// ---------------------------------------------------------------------------
// Orbital elements at J2000.0 — Standish (1992) / Meeus
// ---------------------------------------------------------------------------

struct OrbitalElements {
    l0: f64, l1: f64,
    a: f64,
    e0: f64, e1: f64,
    i0: f64, i1: f64,
    w_upper0: f64, w_upper1: f64, // Ω  (longitude of ascending node)
    w_lower0: f64, w_lower1: f64, // ϖ  (longitude of perihelion)
}

/// Index constants for the ORBITAL_ELEMENTS array.
const MERCURY: usize = 0;
const VENUS: usize = 1;
const EARTH: usize = 2;
const MARS: usize = 3;
const JUPITER: usize = 4;
const SATURN: usize = 5;
const URANUS: usize = 6;
const NEPTUNE: usize = 7;
const PLUTO: usize = 8;

/// Planet names indexed by MERCURY..PLUTO constants.
#[allow(dead_code)]
pub const PLANET_NAMES: [&str; 9] = [
    "mercury", "venus", "earth", "mars", "jupiter",
    "saturn", "uranus", "neptune", "pluto",
];

static ORBITAL_ELEMENTS: [OrbitalElements; 9] = [
    // Mercury
    OrbitalElements {
        l0: 252.25032350, l1: 149472.67411175,
        a: 0.38709927, e0: 0.20563593, e1: 0.00001906,
        i0: 7.00497902, i1: -0.00594749,
        w_upper0: 48.33076593, w_upper1: -0.12534081,
        w_lower0: 77.45779628, w_lower1: 0.16047689,
    },
    // Venus
    OrbitalElements {
        l0: 181.97909950, l1: 58517.81538729,
        a: 0.72333566, e0: 0.00677672, e1: -0.00004107,
        i0: 3.39467605, i1: -0.00078890,
        w_upper0: 76.67984255, w_upper1: -0.27769418,
        w_lower0: 131.60246718, w_lower1: 0.00268329,
    },
    // Earth
    OrbitalElements {
        l0: 100.46457166, l1: 35999.37244981,
        a: 1.00000261, e0: 0.01671123, e1: -0.00004392,
        i0: 0.00001531, i1: -0.01294668,
        w_upper0: 0.0, w_upper1: 0.0,
        w_lower0: 102.93768193, w_lower1: 0.32327364,
    },
    // Mars
    OrbitalElements {
        l0: 355.44656299, l1: 19140.30268499,
        a: 1.52371034, e0: 0.09339410, e1: 0.00007882,
        i0: 1.84969142, i1: -0.00813131,
        w_upper0: 49.55953891, w_upper1: -0.29257343,
        w_lower0: 336.05637041, w_lower1: 0.44441088,
    },
    // Jupiter
    OrbitalElements {
        l0: 34.39644051, l1: 3034.74612775,
        a: 5.20288700, e0: 0.04838624, e1: -0.00013253,
        i0: 1.30439695, i1: -0.00183714,
        w_upper0: 100.47390909, w_upper1: 0.20469106,
        w_lower0: 14.72847983, w_lower1: 0.21252668,
    },
    // Saturn
    OrbitalElements {
        l0: 49.95424423, l1: 1222.49362201,
        a: 9.53667594, e0: 0.05386179, e1: -0.00050991,
        i0: 2.48599187, i1: 0.00193609,
        w_upper0: 113.66242448, w_upper1: -0.28867794,
        w_lower0: 92.59887831, w_lower1: -0.41897216,
    },
    // Uranus
    OrbitalElements {
        l0: 313.23810451, l1: 428.48202785,
        a: 19.18916464, e0: 0.04725744, e1: -0.00004397,
        i0: 0.77263783, i1: -0.00242939,
        w_upper0: 74.01692503, w_upper1: 0.04240589,
        w_lower0: 170.95427630, w_lower1: 0.40805281,
    },
    // Neptune
    OrbitalElements {
        l0: 304.87997031, l1: 218.45945325,
        a: 30.06992276, e0: 0.00859048, e1: 0.00005105,
        i0: 1.77004347, i1: 0.00035372,
        w_upper0: 131.78422574, w_upper1: -0.01299630,
        w_lower0: 44.96476227, w_lower1: -0.32241464,
    },
    // Pluto
    OrbitalElements {
        l0: 238.92903833, l1: 145.20780515,
        a: 39.48211675, e0: 0.24882730, e1: 0.00005170,
        i0: 17.14001206, i1: 0.00004818,
        w_upper0: 110.30393684, w_upper1: -0.01183482,
        w_lower0: 224.06891629, w_lower1: -0.04062942,
    },
];

// ---------------------------------------------------------------------------
// Sun sign date boundaries (traditional tropical zodiac)
// ---------------------------------------------------------------------------

struct SunSignBoundary {
    sign: &'static str,
    start_month: u32,
    start_day: u32,
}

static SUN_SIGN_DATES: [SunSignBoundary; 13] = [
    SunSignBoundary { sign: "capricorn",   start_month: 1,  start_day: 1 },
    SunSignBoundary { sign: "aquarius",    start_month: 1,  start_day: 20 },
    SunSignBoundary { sign: "pisces",      start_month: 2,  start_day: 19 },
    SunSignBoundary { sign: "aries",       start_month: 3,  start_day: 21 },
    SunSignBoundary { sign: "taurus",      start_month: 4,  start_day: 20 },
    SunSignBoundary { sign: "gemini",      start_month: 5,  start_day: 21 },
    SunSignBoundary { sign: "cancer",      start_month: 6,  start_day: 21 },
    SunSignBoundary { sign: "leo",         start_month: 7,  start_day: 23 },
    SunSignBoundary { sign: "virgo",       start_month: 8,  start_day: 23 },
    SunSignBoundary { sign: "libra",       start_month: 9,  start_day: 23 },
    SunSignBoundary { sign: "scorpio",     start_month: 10, start_day: 23 },
    SunSignBoundary { sign: "sagittarius", start_month: 11, start_day: 22 },
    SunSignBoundary { sign: "capricorn",   start_month: 12, start_day: 22 },
];

// ---------------------------------------------------------------------------
// Helper math
// ---------------------------------------------------------------------------

/// Normalise an angle to [0, 360).
fn norm_deg(deg: f64) -> f64 {
    ((deg % 360.0) + 360.0) % 360.0
}

/// Julian centuries since J2000.0.
fn julian_centuries(jd: f64) -> f64 {
    (jd - J2000) / 36525.0
}

// ---------------------------------------------------------------------------
// Julian Day calculation
// ---------------------------------------------------------------------------

/// Convert a calendar date + time to Julian Day Number.
/// Handles both Julian and Gregorian calendars.
pub fn to_julian_day(year: i32, month: u32, day: u32, hour: i32, minute: i32) -> f64 {
    let mut y = year as f64;
    let mut m = month as f64;
    if m <= 2.0 {
        y -= 1.0;
        m += 12.0;
    }
    let a = (y / 100.0).floor();
    let b = 2.0 - a + (a / 4.0).floor();
    let day_fraction = (hour as f64 + minute as f64 / 60.0) / 24.0;

    (365.25 * (y + 4716.0)).floor()
        + (30.6001 * (m + 1.0)).floor()
        + day as f64
        + day_fraction
        + b
        - 1524.5
}

// ---------------------------------------------------------------------------
// Kepler's equation solver (Newton-Raphson)
// ---------------------------------------------------------------------------

/// Solve Kepler's equation  M = E - e·sin(E)  for E (eccentric anomaly).
/// M and E in radians.
pub fn solve_kepler(m: f64, e: f64) -> f64 {
    let mut big_e = m; // initial guess
    for _ in 0..50 {
        let d_e = (big_e - e * big_e.sin() - m) / (1.0 - e * big_e.cos());
        big_e -= d_e;
        if d_e.abs() < 1e-12 {
            break;
        }
    }
    big_e
}

// ---------------------------------------------------------------------------
// Heliocentric ecliptic longitude from orbital elements
// ---------------------------------------------------------------------------

/// Compute heliocentric ecliptic longitude for a planet (by index) at a given
/// Julian Day.
pub fn heliocentric_longitude(planet_idx: usize, jd: f64) -> f64 {
    let el = &ORBITAL_ELEMENTS[planet_idx];
    let t = julian_centuries(jd);

    let l = norm_deg(el.l0 + el.l1 * t);
    let e = el.e0 + el.e1 * t;
    let w_lower = norm_deg(el.w_lower0 + el.w_lower1 * t);
    let w_upper = norm_deg(el.w_upper0 + el.w_upper1 * t);
    let incl = el.i0 + el.i1 * t;

    // Mean anomaly
    let m = norm_deg(l - w_lower);
    let m_rad = m * DEG2RAD;

    // Solve Kepler's equation for eccentric anomaly
    let big_e = solve_kepler(m_rad, e);

    // True anomaly
    let sin_v = ((1.0 - e * e).sqrt() * big_e.sin()) / (1.0 - e * big_e.cos());
    let cos_v = (big_e.cos() - e) / (1.0 - e * big_e.cos());
    let v = sin_v.atan2(cos_v) * RAD2DEG;

    // Heliocentric longitude in the orbital plane
    let l_helio = norm_deg(v + w_lower - w_upper);

    // Convert from orbital plane to ecliptic
    let i_rad = incl * DEG2RAD;
    let l_helio_rad = l_helio * DEG2RAD;

    norm_deg(
        l_helio_rad.sin().atan2(l_helio_rad.cos() / (i_rad.cos()).max(1e-15))
            .min(l_helio_rad.sin().atan2(l_helio_rad.cos()))
            * RAD2DEG
            + w_upper,
    )
}

/// Exact port of the TypeScript `heliocentricLongitude` — alternative form.
#[allow(dead_code)]
fn helio_lon(planet_idx: usize, jd: f64) -> f64 {
    let el = &ORBITAL_ELEMENTS[planet_idx];
    let t = julian_centuries(jd);

    let l = norm_deg(el.l0 + el.l1 * t);
    let e = el.e0 + el.e1 * t;
    let w_lower = norm_deg(el.w_lower0 + el.w_lower1 * t);
    let w_upper = norm_deg(el.w_upper0 + el.w_upper1 * t);
    let incl = el.i0 + el.i1 * t;

    let m = norm_deg(l - w_lower);
    let m_rad = m * DEG2RAD;

    let big_e = solve_kepler(m_rad, e);

    let sin_v = ((1.0 - e * e).sqrt() * big_e.sin()) / (1.0 - e * big_e.cos());
    let cos_v = (big_e.cos() - e) / (1.0 - e * big_e.cos());
    let v = sin_v.atan2(cos_v) * RAD2DEG;

    let l_helio = norm_deg(v + w_lower - w_upper);

    let i_rad = incl * DEG2RAD;
    let l_helio_rad = l_helio * DEG2RAD;

    norm_deg(
        (l_helio_rad.sin() * i_rad.cos()).atan2(l_helio_rad.cos()) * RAD2DEG + w_upper,
    )
}

// ---------------------------------------------------------------------------
// Geocentric ecliptic longitude
// ---------------------------------------------------------------------------

/// Convert heliocentric position to geocentric (as seen from Earth).
/// Uses simplified geometric transformation in the ecliptic plane.
pub fn geocentric_longitude(planet_idx: usize, jd: f64) -> f64 {
    assert!(planet_idx != EARTH, "Cannot compute geocentric longitude of Earth");

    let t = julian_centuries(jd);
    let earth_el = &ORBITAL_ELEMENTS[EARTH];

    // Earth's heliocentric position
    let earth_l = norm_deg(earth_el.l0 + earth_el.l1 * t);
    let earth_e = earth_el.e0 + earth_el.e1 * t;
    let earth_w = norm_deg(earth_el.w_lower0 + earth_el.w_lower1 * t);
    let earth_m = norm_deg(earth_l - earth_w) * DEG2RAD;
    let earth_ecc = solve_kepler(earth_m, earth_e);
    let earth_v = ((1.0 - earth_e * earth_e).sqrt() * earth_ecc.sin())
        .atan2(earth_ecc.cos() - earth_e)
        * RAD2DEG;
    let earth_helio_lon = norm_deg(earth_v + earth_w);
    let earth_r = earth_el.a * (1.0 - earth_e * earth_ecc.cos());

    // Planet's heliocentric position
    let p_el = &ORBITAL_ELEMENTS[planet_idx];
    let p_l = norm_deg(p_el.l0 + p_el.l1 * t);
    let p_e = p_el.e0 + p_el.e1 * t;
    let p_w = norm_deg(p_el.w_lower0 + p_el.w_lower1 * t);
    let p_m = norm_deg(p_l - p_w) * DEG2RAD;
    let p_ecc = solve_kepler(p_m, p_e);
    let p_v = ((1.0 - p_e * p_e).sqrt() * p_ecc.sin())
        .atan2(p_ecc.cos() - p_e)
        * RAD2DEG;
    let p_helio_lon = norm_deg(p_v + p_w);
    let p_r = p_el.a * (1.0 - p_e * p_ecc.cos());

    // Convert to geocentric using simple 2D projection (ecliptic plane)
    let p_helio_rad = p_helio_lon * DEG2RAD;
    let earth_helio_rad = earth_helio_lon * DEG2RAD;

    let x = p_r * p_helio_rad.cos() - earth_r * earth_helio_rad.cos();
    let y = p_r * p_helio_rad.sin() - earth_r * earth_helio_rad.sin();

    norm_deg(y.atan2(x) * RAD2DEG)
}

// ---------------------------------------------------------------------------
// Sun longitude (geocentric)
// ---------------------------------------------------------------------------

/// Compute the Sun's geocentric ecliptic longitude for a given Julian Day.
/// Uses the equation of center from Meeus.
pub fn sun_longitude(jd: f64) -> f64 {
    let t = julian_centuries(jd);

    // Sun's mean longitude
    let l0 = norm_deg(280.46646 + 36000.76983 * t + 0.0003032 * t * t);

    // Sun's mean anomaly
    let m = norm_deg(357.52911 + 35999.05029 * t - 0.0001537 * t * t);
    let m_rad = m * DEG2RAD;

    // Equation of center
    let c = (1.914602 - 0.004817 * t - 0.000014 * t * t) * m_rad.sin()
        + (0.019993 - 0.000101 * t) * (2.0 * m_rad).sin()
        + 0.000289 * (3.0 * m_rad).sin();

    // Sun's true longitude
    let sun_true_lon = norm_deg(l0 + c);

    // Apparent longitude (nutation + aberration)
    let omega = 125.04 - 1934.136 * t;
    let apparent = sun_true_lon - 0.00569 - 0.00478 * (omega * DEG2RAD).sin();

    norm_deg(apparent)
}

// ---------------------------------------------------------------------------
// Moon longitude (simplified — Meeus Ch. 47 principal terms)
// ---------------------------------------------------------------------------

/// Compute the Moon's geocentric ecliptic longitude.
pub fn moon_longitude(jd: f64) -> f64 {
    let t = julian_centuries(jd);

    // Moon's mean longitude
    let lp = norm_deg(
        218.3164477
            + 481267.88123421 * t
            - 0.0015786 * t * t
            + t * t * t / 538841.0
            - t * t * t * t / 65194000.0,
    );

    // Moon's mean elongation
    let d = norm_deg(
        297.8501921
            + 445267.1114034 * t
            - 0.0018819 * t * t
            + t * t * t / 545868.0
            - t * t * t * t / 113065000.0,
    );

    // Sun's mean anomaly
    let m = norm_deg(
        357.5291092 + 35999.0502909 * t - 0.0001536 * t * t + t * t * t / 24490000.0,
    );

    // Moon's mean anomaly
    let mp = norm_deg(
        134.9633964
            + 477198.8675055 * t
            + 0.0087414 * t * t
            + t * t * t / 69699.0
            - t * t * t * t / 14712000.0,
    );

    // Moon's argument of latitude
    let f = norm_deg(
        93.2720950
            + 483202.0175233 * t
            - 0.0036539 * t * t
            - t * t * t / 3526000.0
            + t * t * t * t / 863310000.0,
    );

    let d_rad = d * DEG2RAD;
    let m_rad = m * DEG2RAD;
    let mp_rad = mp * DEG2RAD;
    let f_rad = f * DEG2RAD;

    // Principal terms for longitude (simplified from Meeus Table 47.A)
    let mut sum_l: f64 = 0.0;
    sum_l += 6_288_774.0 * mp_rad.sin();
    sum_l += 1_274_027.0 * (2.0 * d_rad - mp_rad).sin();
    sum_l += 658_314.0 * (2.0 * d_rad).sin();
    sum_l += 213_618.0 * (2.0 * mp_rad).sin();
    sum_l += -185_116.0 * m_rad.sin();
    sum_l += -114_332.0 * (2.0 * f_rad).sin();
    sum_l += 58_793.0 * (2.0 * d_rad - 2.0 * mp_rad).sin();
    sum_l += 57_066.0 * (2.0 * d_rad - m_rad - mp_rad).sin();
    sum_l += 53_322.0 * (2.0 * d_rad + mp_rad).sin();
    sum_l += 45_758.0 * (2.0 * d_rad - m_rad).sin();
    sum_l += -40_923.0 * (m_rad - mp_rad).sin();
    sum_l += -34_720.0 * d_rad.sin();
    sum_l += -30_383.0 * (m_rad + mp_rad).sin();
    sum_l += 15_327.0 * (2.0 * d_rad - 2.0 * f_rad).sin();
    sum_l += -12_528.0 * (mp_rad + 2.0 * f_rad).sin();
    sum_l += 10_980.0 * (mp_rad - 2.0 * f_rad).sin();
    sum_l += 10_675.0 * (4.0 * d_rad - mp_rad).sin();
    sum_l += 10_034.0 * (3.0 * mp_rad).sin();
    sum_l += 8_548.0 * (4.0 * d_rad - 2.0 * mp_rad).sin();
    sum_l += -7_888.0 * (2.0 * d_rad + m_rad - mp_rad).sin();
    sum_l += -6_766.0 * (2.0 * d_rad + m_rad).sin();
    sum_l += -5_163.0 * (d_rad - mp_rad).sin();
    sum_l += 4_987.0 * (d_rad + m_rad).sin();
    sum_l += 4_036.0 * (2.0 * d_rad - m_rad + mp_rad).sin();

    // Convert from 0.000001 degrees to degrees
    norm_deg(lp + sum_l / 1_000_000.0)
}

// ---------------------------------------------------------------------------
// Retrograde detection
// ---------------------------------------------------------------------------

/// Determine if a planet appears retrograde by comparing its longitude
/// one day before and after the given Julian Day.
fn is_retrograde(planet_idx: usize, jd: f64) -> bool {
    let lon_before = geocentric_longitude(planet_idx, jd - 1.0);
    let lon_after = geocentric_longitude(planet_idx, jd + 1.0);

    let mut diff = lon_after - lon_before;
    if diff > 180.0 { diff -= 360.0; }
    if diff < -180.0 { diff += 360.0; }

    diff < 0.0
}

// ---------------------------------------------------------------------------
// Obliquity of the ecliptic
// ---------------------------------------------------------------------------

fn obliquity(jd: f64) -> f64 {
    let t = julian_centuries(jd);
    23.4392911 - 0.0130042 * t - 1.64e-7 * t * t + 5.036e-7 * t * t * t
}

// ---------------------------------------------------------------------------
// Ascendant & Midheaven (MC)
// ---------------------------------------------------------------------------

/// Compute the Local Sidereal Time in degrees for a given JD and geographic
/// longitude.
fn local_sidereal_time(jd: f64, lon_deg: f64) -> f64 {
    let t = julian_centuries(jd);
    let gmst = norm_deg(
        280.46061837
            + 360.98564736629 * (jd - J2000)
            + 0.000387933 * t * t
            - t * t * t / 38710000.0,
    );
    norm_deg(gmst + lon_deg)
}

/// Calculate the Ascendant (rising sign) from LST, latitude, and obliquity.
pub fn compute_ascendant(lst_deg: f64, lat_deg: f64, obl_deg: f64) -> f64 {
    let lst_rad = lst_deg * DEG2RAD;
    let lat_rad = lat_deg * DEG2RAD;
    let obl_rad = obl_deg * DEG2RAD;

    let y = -lst_rad.cos();
    let x = obl_rad.sin() * lat_rad.tan() + obl_rad.cos() * lst_rad.sin();

    norm_deg(y.atan2(x) * RAD2DEG)
}

/// Calculate the Midheaven (Medium Coeli) from LST and obliquity.
pub fn compute_midheaven(lst_deg: f64, obl_deg: f64) -> f64 {
    let lst_rad = lst_deg * DEG2RAD;
    let obl_rad = obl_deg * DEG2RAD;

    let mc = (lst_rad.sin()).atan2(lst_rad.cos() * obl_rad.cos()) * RAD2DEG;
    norm_deg(mc)
}

// ---------------------------------------------------------------------------
// House cusps (Equal house system)
// ---------------------------------------------------------------------------

fn equal_house_cusps(asc_deg: f64) -> Vec<f64> {
    (0..12).map(|i| norm_deg(asc_deg + i as f64 * 30.0)).collect()
}

/// Determine which house (1-12) a planet falls in, given equal house cusps.
fn house_for_longitude(longitude: f64, cusps: &[f64]) -> usize {
    for i in 0..12 {
        let cusp = cusps[i];
        let next_cusp = cusps[(i + 1) % 12];

        if next_cusp > cusp {
            if longitude >= cusp && longitude < next_cusp {
                return i + 1;
            }
        } else {
            // Wraps around 0°
            if longitude >= cusp || longitude < next_cusp {
                return i + 1;
            }
        }
    }
    1 // fallback
}

// ---------------------------------------------------------------------------
// Degrees → zodiac sign
// ---------------------------------------------------------------------------

/// Convert an ecliptic longitude (0–359) to a SignPosition.
pub fn degrees_to_sign(total_degrees: f64) -> SignPosition {
    let deg = norm_deg(total_degrees);
    let sign_index = (deg / 30.0).floor() as usize;
    let within_sign = deg - sign_index as f64 * 30.0;
    SignPosition {
        sign: SIGN_ORDER[sign_index].to_string(),
        degrees: within_sign,
        total_degrees: deg,
    }
}

// ---------------------------------------------------------------------------
// Sun sign from date (calendar-based, traditional boundaries)
// ---------------------------------------------------------------------------

/// Determine the Sun sign from month and day using traditional date boundaries.
/// Quick lookup — no astronomical calculation required.
pub fn calculate_sun_sign(month: u32, day: u32) -> String {
    for boundary in SUN_SIGN_DATES.iter().rev() {
        if month > boundary.start_month
            || (month == boundary.start_month && day >= boundary.start_day)
        {
            return boundary.sign.to_string();
        }
    }
    // Should never reach here; default to Capricorn (Jan 1-19)
    "capricorn".to_string()
}

// ---------------------------------------------------------------------------
// Build a PlanetPosition from a computed ecliptic longitude
// ---------------------------------------------------------------------------

fn build_position(
    planet_name: &str,
    longitude: f64,
    house_cusps: &[f64],
    retrograde: bool,
) -> PlanetPosition {
    let sign_pos = degrees_to_sign(longitude);
    PlanetPosition {
        planet: planet_name.to_string(),
        sign: sign_pos.sign,
        degrees: (sign_pos.degrees * 100.0).round() / 100.0,
        total_degrees: (sign_pos.total_degrees * 100.0).round() / 100.0,
        house: house_for_longitude(longitude, house_cusps),
        retrograde,
    }
}

// ---------------------------------------------------------------------------
// Full natal chart calculation
// ---------------------------------------------------------------------------

/// Calculate a complete natal chart from birth data.
///
/// Uses simplified Keplerian orbital mechanics for planetary positions and
/// standard formulas for the Ascendant, Midheaven, and house cusps. Accuracy
/// is typically within 1-2° for inner planets and the Sun — sufficient for
/// sign determination in most cases.
///
/// # Panics
/// Panics if required fields (`day`, `hour`, `minute`, `latitude`, `longitude`,
/// `timezone`) are `None`.
pub fn calculate_natal_chart(birth_data: &BirthData) -> NatalChart {
    let day = birth_data.day.expect("day is required for natal chart");
    let hour = birth_data.hour.expect("hour is required for natal chart");
    let minute = birth_data.minute.expect("minute is required for natal chart");
    let latitude = birth_data.latitude.expect("latitude is required for natal chart");
    let geo_longitude = birth_data.longitude.expect("longitude is required for natal chart");
    let timezone = birth_data.timezone.expect("timezone is required for natal chart");

    // Convert birth time to UT
    let ut_hour = hour - timezone as i32;
    let ut_minute = minute;

    // Calculate Julian Day
    let jd = to_julian_day(birth_data.year, birth_data.month, day, ut_hour, ut_minute);

    // Obliquity of the ecliptic
    let obl = obliquity(jd);

    // Local Sidereal Time
    let lst = local_sidereal_time(jd, geo_longitude);

    // Ascendant and Midheaven
    let asc_deg = compute_ascendant(lst, latitude, obl);
    let mc_deg = compute_midheaven(lst, obl);

    // House cusps (equal house system)
    let cusps = equal_house_cusps(asc_deg);

    // Compute planetary positions
    let sun_lon = sun_longitude(jd);
    let moon_lon = moon_longitude(jd);
    let mercury_lon = geocentric_longitude(MERCURY, jd);
    let venus_lon = geocentric_longitude(VENUS, jd);
    let mars_lon = geocentric_longitude(MARS, jd);
    let jupiter_lon = geocentric_longitude(JUPITER, jd);
    let saturn_lon = geocentric_longitude(SATURN, jd);
    let uranus_lon = geocentric_longitude(URANUS, jd);
    let neptune_lon = geocentric_longitude(NEPTUNE, jd);
    let pluto_lon = geocentric_longitude(PLUTO, jd);

    // Build planet positions
    let sun = build_position("sun", sun_lon, &cusps, false);
    let moon = build_position("moon", moon_lon, &cusps, false);
    let mercury = build_position("mercury", mercury_lon, &cusps, is_retrograde(MERCURY, jd));
    let venus = build_position("venus", venus_lon, &cusps, is_retrograde(VENUS, jd));
    let mars = build_position("mars", mars_lon, &cusps, is_retrograde(MARS, jd));
    let jupiter = build_position("jupiter", jupiter_lon, &cusps, is_retrograde(JUPITER, jd));
    let saturn = build_position("saturn", saturn_lon, &cusps, is_retrograde(SATURN, jd));
    let uranus = build_position("uranus", uranus_lon, &cusps, is_retrograde(URANUS, jd));
    let neptune = build_position("neptune", neptune_lon, &cusps, is_retrograde(NEPTUNE, jd));
    let pluto = build_position("pluto", pluto_lon, &cusps, is_retrograde(PLUTO, jd));

    // Ascendant and Midheaven as SignPositions
    let ascendant = degrees_to_sign(asc_deg);
    let midheaven = degrees_to_sign(mc_deg);

    // Calculate aspects between all planets
    let all_positions = vec![
        sun.clone(), moon.clone(), mercury.clone(), venus.clone(),
        mars.clone(), jupiter.clone(), saturn.clone(), uranus.clone(),
        neptune.clone(), pluto.clone(),
    ];
    let aspects = calculate_aspects(&all_positions);

    NatalChart {
        sun,
        moon,
        mercury,
        venus,
        mars,
        jupiter,
        saturn,
        uranus,
        neptune,
        pluto,
        ascendant,
        midheaven,
        aspects,
        house_cusps: cusps,
    }
}

// ---------------------------------------------------------------------------
// Aspect calculation
// ---------------------------------------------------------------------------

/// Simple aspect definitions (matching the TypeScript implementation).
struct AspectDef {
    name: &'static str,
    symbol: &'static str,
    degrees: f64,
    orb: f64,
    nature: &'static str,
}

static ASPECT_DEFS: [AspectDef; 5] = [
    AspectDef { name: "Conjunction", symbol: "☌", degrees: 0.0,   orb: 8.0, nature: "neutral" },
    AspectDef { name: "Sextile",    symbol: "⚹", degrees: 60.0,  orb: 6.0, nature: "harmonious" },
    AspectDef { name: "Square",     symbol: "□", degrees: 90.0,  orb: 8.0, nature: "challenging" },
    AspectDef { name: "Trine",      symbol: "△", degrees: 120.0, orb: 8.0, nature: "harmonious" },
    AspectDef { name: "Opposition", symbol: "☍", degrees: 180.0, orb: 8.0, nature: "challenging" },
];

/// Calculate all aspects between planet positions.
pub fn calculate_aspects(positions: &[PlanetPosition]) -> Vec<ChartAspect> {
    let mut aspects = Vec::new();

    for i in 0..positions.len() {
        for j in (i + 1)..positions.len() {
            let p1 = &positions[i];
            let p2 = &positions[j];

            let mut separation = (p1.total_degrees - p2.total_degrees).abs();
            if separation > 180.0 {
                separation = 360.0 - separation;
            }

            for def in &ASPECT_DEFS {
                let orb_distance = (separation - def.degrees).abs();
                if orb_distance <= def.orb {
                    aspects.push(ChartAspect {
                        planet1: p1.planet.clone(),
                        planet2: p2.planet.clone(),
                        aspect_name: def.name.to_string(),
                        aspect_symbol: def.symbol.to_string(),
                        exact_degrees: def.degrees,
                        actual_degrees: separation,
                        orb: (orb_distance * 100.0).round() / 100.0,
                        nature: def.nature.to_string(),
                    });
                }
            }
        }
    }

    // Sort by tightest orb first
    aspects.sort_by(|a, b| a.orb.partial_cmp(&b.orb).unwrap_or(std::cmp::Ordering::Equal));
    aspects
}

// ---------------------------------------------------------------------------
// AstrologyEngine — stateful wrapper
// ---------------------------------------------------------------------------

pub struct AstrologyEngine;

impl AstrologyEngine {
    pub fn new() -> Self {
        Self
    }

    /// Convert calendar date/time to Julian Day number.
    pub fn to_julian_day(&self, year: i32, month: u32, day: u32, hour: i32, minute: i32) -> f64 {
        to_julian_day(year, month, day, hour, minute)
    }

    /// Determine the Sun sign from month/day (traditional date boundaries).
    pub fn calculate_sun_sign(&self, month: u32, day: u32) -> String {
        calculate_sun_sign(month, day)
    }

    /// Calculate a complete natal chart from birth data.
    pub fn calculate_natal_chart(&self, birth_data: &BirthData) -> NatalChart {
        calculate_natal_chart(birth_data)
    }

    /// Sun's geocentric ecliptic longitude at a given Julian Day.
    pub fn sun_longitude(&self, jd: f64) -> f64 {
        sun_longitude(jd)
    }

    /// Moon's geocentric ecliptic longitude at a given Julian Day.
    pub fn moon_longitude(&self, jd: f64) -> f64 {
        moon_longitude(jd)
    }

    /// Compute the Ascendant from LST, latitude, and obliquity.
    pub fn compute_ascendant(&self, lst_deg: f64, lat_deg: f64, obl_deg: f64) -> f64 {
        compute_ascendant(lst_deg, lat_deg, obl_deg)
    }

    /// Compute the Midheaven from LST and obliquity.
    pub fn compute_midheaven(&self, lst_deg: f64, obl_deg: f64) -> f64 {
        compute_midheaven(lst_deg, obl_deg)
    }

    /// Convert ecliptic degrees to a SignPosition.
    pub fn degrees_to_sign(&self, total_degrees: f64) -> SignPosition {
        degrees_to_sign(total_degrees)
    }
}

impl Default for AstrologyEngine {
    fn default() -> Self {
        Self::new()
    }
}

// ---------------------------------------------------------------------------
// Unit tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn julian_day_j2000() {
        // J2000.0 = 2000-01-01 12:00 TT → JD 2451545.0
        let jd = to_julian_day(2000, 1, 1, 12, 0);
        assert!((jd - 2_451_545.0).abs() < 0.001, "J2000.0 JD mismatch: {}", jd);
    }

    #[test]
    fn julian_day_known_date() {
        // 1957-10-04 19:28 UT → JD 2436116.31111 (Sputnik launch)
        let jd = to_julian_day(1957, 10, 4, 19, 28);
        assert!((jd - 2_436_116.31111).abs() < 0.001, "Sputnik JD mismatch: {}", jd);
    }

    #[test]
    fn kepler_circular_orbit() {
        // e = 0 → E should equal M
        let m = 1.0_f64;
        let e_result = solve_kepler(m, 0.0);
        assert!((e_result - m).abs() < 1e-10);
    }

    #[test]
    fn sun_sign_known_dates() {
        assert_eq!(calculate_sun_sign(3, 25), "aries");
        assert_eq!(calculate_sun_sign(7, 4), "cancer");
        assert_eq!(calculate_sun_sign(12, 25), "capricorn");
        assert_eq!(calculate_sun_sign(1, 15), "capricorn");
        assert_eq!(calculate_sun_sign(2, 20), "pisces");
        assert_eq!(calculate_sun_sign(8, 15), "leo");
    }

    #[test]
    fn degrees_to_sign_basics() {
        let pos = degrees_to_sign(0.0);
        assert_eq!(pos.sign, "aries");

        let pos2 = degrees_to_sign(45.0);
        assert_eq!(pos2.sign, "taurus");

        let pos3 = degrees_to_sign(270.0);
        assert_eq!(pos3.sign, "capricorn");
    }

    #[test]
    fn natal_chart_known_birth() {
        // Test with a known date: 1990-06-15 14:30, New York (40.7128°N, -74.0060°W, UTC-4)
        let birth = BirthData {
            year: 1990,
            month: 6,
            day: Some(15),
            hour: Some(14),
            minute: Some(30),
            latitude: Some(40.7128),
            longitude: Some(-74.0060),
            timezone: Some(-4.0),
        };

        let chart = calculate_natal_chart(&birth);

        // Sun should be in Gemini (roughly 84° ecliptic longitude)
        assert_eq!(chart.sun.sign, "gemini", "Sun sign mismatch");

        // Should have 12 house cusps
        assert_eq!(chart.house_cusps.len(), 12);
    }

    #[test]
    fn sun_longitude_j2000() {
        // At J2000.0, Sun should be near ~280° (Capricorn)
        let jd = to_julian_day(2000, 1, 1, 12, 0);
        let lon = sun_longitude(jd);
        // The Sun was at about 280.5° on 2000-01-01
        assert!(lon > 279.0 && lon < 282.0, "Sun at J2000.0 = {}°", lon);
    }

    #[test]
    fn engine_api() {
        let engine = AstrologyEngine::new();
        assert_eq!(engine.calculate_sun_sign(3, 25), "aries");

        let pos = engine.degrees_to_sign(120.0);
        assert_eq!(pos.sign, "leo");
    }
}
