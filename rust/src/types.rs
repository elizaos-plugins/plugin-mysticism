use serde::{Deserialize, Serialize};

// ---------------------------------------------------------------------------
// Tarot types
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TarotCard {
    pub id: String,
    pub name: String,
    pub number: i32,
    pub arcana: String,
    /// null for major arcana cards
    pub suit: Option<String>,
    pub keywords_upright: Vec<String>,
    pub keywords_reversed: Vec<String>,
    pub meaning_upright: String,
    pub meaning_reversed: String,
    pub description: String,
    pub element: String,
    pub planet: Option<String>,
    pub zodiac: Option<String>,
    pub numerology: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DrawnCard {
    pub card: TarotCard,
    pub reversed: bool,
    pub position_index: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpreadPosition {
    pub index: usize,
    pub name: String,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpreadDefinition {
    pub id: String,
    pub name: String,
    pub description: String,
    pub positions: Vec<SpreadPosition>,
    #[serde(rename = "cardCount")]
    pub card_count: usize,
}

// ---------------------------------------------------------------------------
// I Ching types
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Trigram {
    pub number: u32,
    pub name: String,
    #[serde(rename = "englishName")]
    pub english_name: String,
    pub character: String,
    pub binary: String,
    pub lines: Vec<u8>,
    pub attribute: String,
    pub image: String,
    pub family: String,
    pub element: String,
    pub direction: String,
    #[serde(rename = "bodyPart")]
    pub body_part: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HexagramLine {
    pub position: u32,
    pub text: String,
    pub meaning: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Hexagram {
    pub number: u32,
    pub name: String,
    #[serde(rename = "englishName")]
    pub english_name: String,
    pub character: String,
    pub binary: String,
    #[serde(rename = "topTrigram")]
    pub top_trigram: u32,
    #[serde(rename = "bottomTrigram")]
    pub bottom_trigram: u32,
    pub judgment: String,
    pub image: String,
    pub lines: Vec<HexagramLine>,
    pub keywords: Vec<String>,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CastResult {
    /// Raw coin-sum values for each of the 6 lines (6, 7, 8, or 9)
    pub lines: Vec<u8>,
    /// 1-based positions of changing lines
    pub changing_lines: Vec<usize>,
    pub hexagram_number: u32,
    pub transformed_hexagram_number: Option<u32>,
    pub binary: String,
    pub transformed_binary: Option<String>,
}

// ---------------------------------------------------------------------------
// Astrology types
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BirthData {
    pub year: i32,
    /// 1-12
    pub month: u32,
    /// 1-31, optional (nullable)
    pub day: Option<u32>,
    /// 0-23, optional
    pub hour: Option<i32>,
    /// 0-59, optional
    pub minute: Option<i32>,
    /// Decimal degrees, north positive; optional
    pub latitude: Option<f64>,
    /// Decimal degrees, east positive; optional
    pub longitude: Option<f64>,
    /// UTC offset in hours (e.g. -5 for EST); optional
    pub timezone: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlanetPosition {
    pub planet: String,
    pub sign: String,
    /// 0-29 within sign
    pub degrees: f64,
    /// 0-359 ecliptic longitude
    pub total_degrees: f64,
    /// 1-12
    pub house: usize,
    pub retrograde: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SignPosition {
    pub sign: String,
    /// 0-29 within sign
    pub degrees: f64,
    /// 0-359 on the ecliptic
    pub total_degrees: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChartAspect {
    pub planet1: String,
    pub planet2: String,
    pub aspect_name: String,
    pub aspect_symbol: String,
    pub exact_degrees: f64,
    pub actual_degrees: f64,
    pub orb: f64,
    pub nature: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NatalChart {
    pub sun: PlanetPosition,
    pub moon: PlanetPosition,
    pub mercury: PlanetPosition,
    pub venus: PlanetPosition,
    pub mars: PlanetPosition,
    pub jupiter: PlanetPosition,
    pub saturn: PlanetPosition,
    pub uranus: PlanetPosition,
    pub neptune: PlanetPosition,
    pub pluto: PlanetPosition,
    pub ascendant: SignPosition,
    pub midheaven: SignPosition,
    pub aspects: Vec<ChartAspect>,
    pub house_cusps: Vec<f64>,
}

// ---------------------------------------------------------------------------
// Feedback
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FeedbackEntry {
    pub element: String,
    pub user_text: String,
    pub timestamp: u64,
}
