use elizaos_plugin_mysticism::engines::astrology;
use elizaos_plugin_mysticism::engines::iching;
use elizaos_plugin_mysticism::engines::tarot;
use elizaos_plugin_mysticism::types::BirthData;
use elizaos_plugin_mysticism::{AstrologyEngine, IChingEngine, TarotEngine};
use pretty_assertions::assert_eq;

// ---------------------------------------------------------------------------
// Tarot smoke tests
// ---------------------------------------------------------------------------

#[test]
fn deck_has_78_cards() {
    let deck = tarot::create_deck();
    assert_eq!(deck.len(), 78);
}

#[test]
fn draw_and_shuffle() {
    let mut deck = tarot::create_deck();
    tarot::shuffle_deck(&mut deck);
    let drawn = tarot::draw_cards(&deck, 5, true).unwrap();
    assert_eq!(drawn.len(), 5);
}

#[test]
fn tarot_engine_spreads() {
    let engine = TarotEngine::new();
    let spreads = engine.get_spreads();
    assert!(!spreads.is_empty(), "Should have at least one spread");
    let celtic = engine.get_spread("celtic_cross").expect("Celtic Cross spread should exist");
    assert_eq!(celtic.card_count, 10);
}

// ---------------------------------------------------------------------------
// I Ching smoke tests
// ---------------------------------------------------------------------------

#[test]
fn cast_hexagram_produces_valid_result() {
    let result = iching::cast_hexagram();
    assert_eq!(result.lines.len(), 6);
    for &line in &result.lines {
        assert!(
            [6, 7, 8, 9].contains(&line),
            "Line value must be 6, 7, 8, or 9 — got {}",
            line
        );
    }
    assert!(
        (1..=64).contains(&result.hexagram_number),
        "Hexagram number must be 1-64, got {}",
        result.hexagram_number
    );
    assert_eq!(result.binary.len(), 6);
}

#[test]
fn hexagram_lookup() {
    let hex = iching::get_hexagram(1).unwrap();
    assert_eq!(hex.name, "Qian");
    assert_eq!(hex.english_name, "The Creative");
}

#[test]
fn iching_engine_trigrams() {
    let engine = IChingEngine::new();
    let hex = engine.get_hexagram(1).expect("Hexagram 1 should exist");
    let upper = engine.get_upper_trigram(hex).expect("Upper trigram should exist");
    let lower = engine.get_lower_trigram(hex).expect("Lower trigram should exist");
    // Hexagram 1 (Qian) is heaven/heaven
    assert_eq!(upper.name, "Qian");
    assert_eq!(lower.name, "Qian");
}

// ---------------------------------------------------------------------------
// Astrology smoke tests
// ---------------------------------------------------------------------------

#[test]
fn known_birth_date_produces_expected_sun_sign() {
    // March 25 → Aries
    assert_eq!(astrology::calculate_sun_sign(3, 25), "aries");
    // July 4 → Cancer
    assert_eq!(astrology::calculate_sun_sign(7, 4), "cancer");
    // December 25 → Capricorn
    assert_eq!(astrology::calculate_sun_sign(12, 25), "capricorn");
    // January 15 → Capricorn
    assert_eq!(astrology::calculate_sun_sign(1, 15), "capricorn");
    // February 20 → Pisces
    assert_eq!(astrology::calculate_sun_sign(2, 20), "pisces");
}

#[test]
fn julian_day_j2000() {
    let jd = astrology::to_julian_day(2000, 1, 1, 12, 0);
    assert!((jd - 2_451_545.0).abs() < 0.001);
}

#[test]
fn natal_chart_sun_in_gemini() {
    // 1990-06-15 14:30 in New York
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

    let chart = astrology::calculate_natal_chart(&birth);
    assert_eq!(chart.sun.sign, "gemini", "Sun should be in Gemini");
    assert_eq!(chart.house_cusps.len(), 12, "Should have 12 house cusps");
}

#[test]
fn astrology_engine_api() {
    let engine = AstrologyEngine::new();

    let sign = engine.calculate_sun_sign(8, 15);
    assert_eq!(sign, "leo");

    let pos = engine.degrees_to_sign(0.0);
    assert_eq!(pos.sign, "aries");

    let pos2 = engine.degrees_to_sign(120.0);
    assert_eq!(pos2.sign, "leo");
}
