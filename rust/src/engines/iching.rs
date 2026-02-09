use std::collections::HashMap;

use rand::Rng;

use crate::types::{CastResult, Hexagram, Trigram};

// ---------------------------------------------------------------------------
// Static data loaded at compile time
// ---------------------------------------------------------------------------

const HEXAGRAMS_JSON: &str = include_str!("../../../data/iching/hexagrams.json");
const TRIGRAMS_JSON: &str = include_str!("../../../data/iching/trigrams.json");

fn load_hexagrams() -> Vec<Hexagram> {
    serde_json::from_str(HEXAGRAMS_JSON).expect("Failed to parse hexagrams.json")
}

fn load_trigrams() -> Vec<Trigram> {
    serde_json::from_str(TRIGRAMS_JSON).expect("Failed to parse trigrams.json")
}

// ---------------------------------------------------------------------------
// Line helpers
// ---------------------------------------------------------------------------

/// Three-coin toss result for a single line.
struct CastLineResult {
    /// Raw coin sum: 6, 7, 8, or 9
    value: u8,
    /// Whether this line is a changing line
    changing: bool,
}

/// Three coins are tossed.  Heads = 3, Tails = 2.
/// Sum determines line type:
///   6 (2+2+2) = Old Yin   — changing broken line
///   7 (2+2+3) = Young Yang — stable solid line
///   8 (2+3+3) = Young Yin  — stable broken line
///   9 (3+3+3) = Old Yang   — changing solid line
fn cast_line() -> CastLineResult {
    let mut rng = rand::thread_rng();
    let coin = |rng: &mut rand::rngs::ThreadRng| -> u8 {
        if rng.gen_bool(0.5) { 3 } else { 2 }
    };
    let c1 = coin(&mut rng);
    let c2 = coin(&mut rng);
    let c3 = coin(&mut rng);
    let value = c1 + c2 + c3;

    CastLineResult {
        value,
        changing: value == 6 || value == 9,
    }
}

/// Map a line value to its binary digit.
/// 7 and 9 are yang (solid) → 1
/// 6 and 8 are yin (broken) → 0
fn line_value_to_binary(value: u8) -> u8 {
    if value == 7 || value == 9 { 1 } else { 0 }
}

/// Map a line value to its *transformed* binary digit.
/// Old Yin (6) → Yang (1)
/// Old Yang (9) → Yin (0)
/// Young lines stay the same.
fn line_value_to_transformed_binary(value: u8) -> u8 {
    match value {
        6 => 1, // Old Yin → Yang
        9 => 0, // Old Yang → Yin
        _ => line_value_to_binary(value),
    }
}

// ---------------------------------------------------------------------------
// Public free functions
// ---------------------------------------------------------------------------

/// Cast a full hexagram using the three-coin method.
/// Lines are cast from bottom (position 1) to top (position 6).
pub fn cast_hexagram() -> CastResult {
    let cast_lines: Vec<CastLineResult> = (0..6).map(|_| cast_line()).collect();

    let lines: Vec<u8> = cast_lines.iter().map(|cl| cl.value).collect();
    let changing_lines: Vec<usize> = cast_lines
        .iter()
        .enumerate()
        .filter_map(|(i, cl)| if cl.changing { Some(i + 1) } else { None })
        .collect();

    // Build binary string (bottom to top = left to right)
    let binary: String = cast_lines
        .iter()
        .map(|cl| line_value_to_binary(cl.value).to_string())
        .collect();

    let hexagrams = load_hexagrams();
    let binary_to_number: HashMap<String, u32> =
        hexagrams.iter().map(|h| (h.binary.clone(), h.number)).collect();

    let hexagram_number = *binary_to_number
        .get(&binary)
        .unwrap_or_else(|| panic!("Unknown hexagram binary pattern: {}", binary));

    let (transformed_hexagram_number, transformed_binary) = if !changing_lines.is_empty() {
        let tb: String = cast_lines
            .iter()
            .map(|cl| line_value_to_transformed_binary(cl.value).to_string())
            .collect();
        let tn = *binary_to_number
            .get(&tb)
            .unwrap_or_else(|| panic!("Unknown hexagram binary pattern: {}", tb));
        (Some(tn), Some(tb))
    } else {
        (None, None)
    };

    CastResult {
        lines,
        changing_lines,
        hexagram_number,
        transformed_hexagram_number,
        binary,
        transformed_binary,
    }
}

/// Convert a binary string (e.g. "111111") to a hexagram number.
pub fn binary_to_hexagram_number(binary: &str) -> Result<u32, String> {
    let hexagrams = load_hexagrams();
    hexagrams
        .iter()
        .find(|h| h.binary == binary)
        .map(|h| h.number)
        .ok_or_else(|| format!("Unknown hexagram binary pattern: {}", binary))
}

/// Get a hexagram by its King Wen sequence number (1–64).
pub fn get_hexagram(number: u32) -> Result<Hexagram, String> {
    let hexagrams = load_hexagrams();
    hexagrams
        .into_iter()
        .find(|h| h.number == number)
        .ok_or_else(|| format!("Hexagram number {} not found (valid range: 1-64)", number))
}

/// Get a trigram by its number (1–8).
pub fn get_trigram(number: u32) -> Result<Trigram, String> {
    let trigrams = load_trigrams();
    trigrams
        .into_iter()
        .find(|t| t.number == number)
        .ok_or_else(|| format!("Trigram number {} not found (valid range: 1-8)", number))
}

/// Get the lower (bottom) trigram of a hexagram.
pub fn get_lower_trigram(hexagram: &Hexagram) -> Result<Trigram, String> {
    get_trigram(hexagram.bottom_trigram)
}

/// Get the upper (top) trigram of a hexagram.
pub fn get_upper_trigram(hexagram: &Hexagram) -> Result<Trigram, String> {
    get_trigram(hexagram.top_trigram)
}

// ---------------------------------------------------------------------------
// IChingEngine — stateful wrapper
// ---------------------------------------------------------------------------

pub struct IChingEngine {
    hexagrams: Vec<Hexagram>,
    trigrams: Vec<Trigram>,
    binary_to_number: HashMap<String, u32>,
}

impl IChingEngine {
    pub fn new() -> Self {
        let hexagrams = load_hexagrams();
        let trigrams = load_trigrams();
        let binary_to_number: HashMap<String, u32> =
            hexagrams.iter().map(|h| (h.binary.clone(), h.number)).collect();

        Self {
            hexagrams,
            trigrams,
            binary_to_number,
        }
    }

    /// Cast a full hexagram using the three-coin method.
    pub fn cast_hexagram(&self) -> CastResult {
        let cast_lines: Vec<CastLineResult> = (0..6).map(|_| cast_line()).collect();

        let lines: Vec<u8> = cast_lines.iter().map(|cl| cl.value).collect();
        let changing_lines: Vec<usize> = cast_lines
            .iter()
            .enumerate()
            .filter_map(|(i, cl)| if cl.changing { Some(i + 1) } else { None })
            .collect();

        let binary: String = cast_lines
            .iter()
            .map(|cl| line_value_to_binary(cl.value).to_string())
            .collect();

        let hexagram_number = *self
            .binary_to_number
            .get(&binary)
            .unwrap_or_else(|| panic!("Unknown hexagram binary pattern: {}", binary));

        let (transformed_hexagram_number, transformed_binary) = if !changing_lines.is_empty() {
            let tb: String = cast_lines
                .iter()
                .map(|cl| line_value_to_transformed_binary(cl.value).to_string())
                .collect();
            let tn = *self
                .binary_to_number
                .get(&tb)
                .unwrap_or_else(|| panic!("Unknown hexagram binary pattern: {}", tb));
            (Some(tn), Some(tb))
        } else {
            (None, None)
        };

        CastResult {
            lines,
            changing_lines,
            hexagram_number,
            transformed_hexagram_number,
            binary,
            transformed_binary,
        }
    }

    /// Look up a hexagram by King Wen number.
    pub fn get_hexagram(&self, number: u32) -> Option<&Hexagram> {
        self.hexagrams.iter().find(|h| h.number == number)
    }

    /// Look up a trigram by number.
    pub fn get_trigram(&self, number: u32) -> Option<&Trigram> {
        self.trigrams.iter().find(|t| t.number == number)
    }

    /// Convert a binary pattern to a hexagram number.
    pub fn binary_to_hexagram_number(&self, binary: &str) -> Option<u32> {
        self.binary_to_number.get(binary).copied()
    }

    /// Get the lower (bottom) trigram of a hexagram.
    pub fn get_lower_trigram(&self, hexagram: &Hexagram) -> Option<&Trigram> {
        self.get_trigram(hexagram.bottom_trigram)
    }

    /// Get the upper (top) trigram of a hexagram.
    pub fn get_upper_trigram(&self, hexagram: &Hexagram) -> Option<&Trigram> {
        self.get_trigram(hexagram.top_trigram)
    }
}

impl Default for IChingEngine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn loads_64_hexagrams() {
        let hexagrams = load_hexagrams();
        assert_eq!(hexagrams.len(), 64);
    }

    #[test]
    fn loads_8_trigrams() {
        let trigrams = load_trigrams();
        assert_eq!(trigrams.len(), 8);
    }

    #[test]
    fn cast_hexagram_produces_valid_result() {
        let result = cast_hexagram();
        assert_eq!(result.lines.len(), 6);
        for &line in &result.lines {
            assert!(
                line == 6 || line == 7 || line == 8 || line == 9,
                "Line value must be 6, 7, 8, or 9 — got {}",
                line
            );
        }
        assert!(
            (1..=64).contains(&result.hexagram_number),
            "Hexagram number must be 1-64"
        );
        assert_eq!(result.binary.len(), 6);
    }

    #[test]
    fn hexagram_1_is_qian() {
        let hex = get_hexagram(1).unwrap();
        assert_eq!(hex.name, "Qian");
        assert_eq!(hex.binary, "111111");
    }

    #[test]
    fn trigram_1_is_qian() {
        let tri = get_trigram(1).unwrap();
        assert_eq!(tri.name, "Qian");
        assert_eq!(tri.binary, "111");
    }

    #[test]
    fn binary_lookup() {
        let n = binary_to_hexagram_number("000000").unwrap();
        assert_eq!(n, 2); // Kun / The Receptive
    }

    #[test]
    fn engine_cast_hexagram() {
        let engine = IChingEngine::new();
        let result = engine.cast_hexagram();
        assert_eq!(result.lines.len(), 6);
        assert!((1..=64).contains(&result.hexagram_number));
    }
}
