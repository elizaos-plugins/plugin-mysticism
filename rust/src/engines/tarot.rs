use rand::seq::SliceRandom;
use rand::Rng;

use crate::types::{DrawnCard, SpreadDefinition, TarotCard};

// ---------------------------------------------------------------------------
// Static data loaded at compile time
// ---------------------------------------------------------------------------

const CARDS_JSON: &str = include_str!("../../../data/tarot/cards.json");
const SPREADS_JSON: &str = include_str!("../../../data/tarot/spreads.json");

fn load_cards() -> Vec<TarotCard> {
    serde_json::from_str(CARDS_JSON).expect("Failed to parse cards.json")
}

fn load_spreads() -> Vec<SpreadDefinition> {
    serde_json::from_str(SPREADS_JSON).expect("Failed to parse spreads.json")
}

// ---------------------------------------------------------------------------
// Public free functions
// ---------------------------------------------------------------------------

/// Create a fresh 78-card deck from the embedded JSON data.
pub fn create_deck() -> Vec<TarotCard> {
    load_cards()
}

/// Fisher-Yates shuffle using `rand::thread_rng()` (OsRng-backed).
pub fn shuffle_deck(cards: &mut Vec<TarotCard>) {
    let mut rng = rand::thread_rng();
    cards.shuffle(&mut rng);
}

/// Draw `count` cards from the top of the deck.
///
/// If `allow_reversals` is true, each card has a 50 % chance of being reversed.
///
/// # Errors
/// Returns an error string if `count` exceeds the deck size.
pub fn draw_cards(
    deck: &[TarotCard],
    count: usize,
    allow_reversals: bool,
) -> Result<Vec<DrawnCard>, String> {
    if count > deck.len() {
        return Err(format!(
            "Cannot draw {} cards from a deck of {}",
            count,
            deck.len()
        ));
    }

    let mut rng = rand::thread_rng();
    let mut drawn = Vec::with_capacity(count);

    for i in 0..count {
        let reversed = if allow_reversals {
            rng.gen_bool(0.5)
        } else {
            false
        };
        drawn.push(DrawnCard {
            card: deck[i].clone(),
            reversed,
            position_index: i,
        });
    }

    Ok(drawn)
}

/// Look up a card by its id (e.g. `"major_00_fool"`).
pub fn get_card(deck: &[TarotCard], id: &str) -> Option<TarotCard> {
    deck.iter().find(|c| c.id == id).cloned()
}

/// Filter cards by arcana and/or suit.
pub fn filter_cards(
    deck: &[TarotCard],
    arcana: Option<&str>,
    suit: Option<&str>,
) -> Vec<TarotCard> {
    deck.iter()
        .filter(|c| {
            if let Some(a) = arcana {
                if c.arcana != a {
                    return false;
                }
            }
            if let Some(s) = suit {
                match &c.suit {
                    Some(cs) if cs == s => {}
                    _ => return false,
                }
            }
            true
        })
        .cloned()
        .collect()
}

// ---------------------------------------------------------------------------
// TarotEngine — stateful wrapper
// ---------------------------------------------------------------------------

pub struct TarotEngine {
    deck: Vec<TarotCard>,
    spreads: Vec<SpreadDefinition>,
}

impl TarotEngine {
    pub fn new() -> Self {
        Self {
            deck: load_cards(),
            spreads: load_spreads(),
        }
    }

    /// Return a copy of the full 78-card deck.
    pub fn create_deck(&self) -> Vec<TarotCard> {
        self.deck.clone()
    }

    /// Shuffle a deck in-place using Fisher-Yates.
    pub fn shuffle_deck(&self, cards: &mut Vec<TarotCard>) {
        shuffle_deck(cards);
    }

    /// Draw `count` cards from the given deck.
    pub fn draw_cards(
        &self,
        deck: &[TarotCard],
        count: usize,
        allow_reversals: bool,
    ) -> Result<Vec<DrawnCard>, String> {
        draw_cards(deck, count, allow_reversals)
    }

    /// Look up a card by id in the master deck.
    pub fn get_card(&self, id: &str) -> Option<TarotCard> {
        get_card(&self.deck, id)
    }

    /// Filter the master deck by arcana / suit.
    pub fn filter_cards(&self, arcana: Option<&str>, suit: Option<&str>) -> Vec<TarotCard> {
        filter_cards(&self.deck, arcana, suit)
    }

    /// Return all available spread definitions.
    pub fn get_spreads(&self) -> &[SpreadDefinition] {
        &self.spreads
    }

    /// Look up a spread by id.
    pub fn get_spread(&self, id: &str) -> Option<&SpreadDefinition> {
        self.spreads.iter().find(|s| s.id == id)
    }
}

impl Default for TarotEngine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn deck_has_78_cards() {
        let deck = create_deck();
        assert_eq!(deck.len(), 78);
    }

    #[test]
    fn shuffle_changes_order() {
        let mut deck = create_deck();
        let original_first = deck[0].id.clone();
        // Shuffle many times — statistically the first card should change
        let mut changed = false;
        for _ in 0..20 {
            shuffle_deck(&mut deck);
            if deck[0].id != original_first {
                changed = true;
                break;
            }
        }
        assert!(changed, "Shuffle should change deck order");
    }

    #[test]
    fn draw_respects_count() {
        let deck = create_deck();
        let drawn = draw_cards(&deck, 3, false).unwrap();
        assert_eq!(drawn.len(), 3);
    }

    #[test]
    fn draw_too_many_errors() {
        let deck = create_deck();
        let result = draw_cards(&deck, 100, false);
        assert!(result.is_err());
    }

    #[test]
    fn filter_major_arcana() {
        let deck = create_deck();
        let major = filter_cards(&deck, Some("major"), None);
        assert_eq!(major.len(), 22);
    }

    #[test]
    fn filter_by_suit() {
        let deck = create_deck();
        let wands = filter_cards(&deck, Some("minor"), Some("wands"));
        assert_eq!(wands.len(), 14);
    }

    #[test]
    fn engine_get_spread() {
        let engine = TarotEngine::new();
        let celtic = engine.get_spread("celtic_cross");
        assert!(celtic.is_some());
        assert_eq!(celtic.unwrap().card_count, 10);
    }
}
