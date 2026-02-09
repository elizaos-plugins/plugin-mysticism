"""Smoke tests for the Tarot engine."""

import sys
from pathlib import Path

# Ensure the package is importable when running from the tests/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elizaos_plugin_mysticism.engines.tarot import (
    TarotEngine,
    create_deck,
    draw_cards,
    get_all_spreads,
    get_spread,
    shuffle_deck,
)
from elizaos_plugin_mysticism.types import FeedbackEntry


# ------------------------------------------------------------------
# Deck basics
# ------------------------------------------------------------------


def test_deck_has_78_cards():
    deck = create_deck()
    assert len(deck) == 78


def test_major_arcana_count():
    deck = create_deck()
    majors = [c for c in deck if c.arcana == "major"]
    assert len(majors) == 22


def test_minor_arcana_count():
    deck = create_deck()
    minors = [c for c in deck if c.arcana == "minor"]
    assert len(minors) == 56


# ------------------------------------------------------------------
# Shuffle & draw
# ------------------------------------------------------------------


def test_shuffle_preserves_length():
    deck = create_deck()
    shuffled = shuffle_deck(deck)
    assert len(shuffled) == 78


def test_shuffle_changes_order():
    deck = create_deck()
    shuffled = shuffle_deck(deck)
    # Extremely unlikely all 78 cards stay in the same position
    ids_before = [c.id for c in deck]
    ids_after = [c.id for c in shuffled]
    assert ids_before != ids_after


def test_draw_returns_correct_count():
    deck = shuffle_deck(create_deck())
    drawn = draw_cards(deck, 3)
    assert len(drawn) == 3
    for i, dc in enumerate(drawn):
        assert dc.positionIndex == i


def test_draw_zero():
    deck = shuffle_deck(create_deck())
    drawn = draw_cards(deck, 0)
    assert len(drawn) == 0


def test_draw_too_many_raises():
    deck = shuffle_deck(create_deck())
    try:
        draw_cards(deck, 100)
        assert False, "Expected ValueError"
    except ValueError:
        pass


# ------------------------------------------------------------------
# Spreads
# ------------------------------------------------------------------


def test_spreads_loaded():
    spreads = get_all_spreads()
    assert len(spreads) > 0


def test_single_card_spread():
    spread = get_spread("single")
    assert spread is not None
    assert spread.cardCount == 1


def test_three_card_spread():
    spread = get_spread("three_card")
    assert spread is not None
    assert spread.cardCount == 3


# ------------------------------------------------------------------
# Engine lifecycle
# ------------------------------------------------------------------


def test_engine_start_reading():
    engine = TarotEngine()
    state = engine.start_reading("three_card", "What should I focus on?")
    assert len(state.drawnCards) == 3
    assert state.revealedIndex == 0
    assert state.question == "What should I focus on?"


def test_engine_reveal_cycle():
    engine = TarotEngine()
    state = engine.start_reading("single", "Quick guidance")

    assert not engine.is_complete(state)

    reveal = engine.get_next_reveal(state)
    assert reveal is not None
    assert "card" in reveal

    feedback = FeedbackEntry(element="card_0", userText="Interesting", timestamp=0)
    state = engine.record_feedback(state, feedback)

    assert engine.is_complete(state)
    assert engine.get_next_reveal(state) is None


def test_engine_synthesis():
    engine = TarotEngine()
    state = engine.start_reading("single", "Daily guidance")

    feedback = FeedbackEntry(element="card_0", userText="I see", timestamp=0)
    state = engine.record_feedback(state, feedback)

    synthesis = engine.get_synthesis(state)
    assert "spread" in synthesis
    assert "cards" in synthesis


def test_engine_unknown_spread_raises():
    engine = TarotEngine()
    try:
        engine.start_reading("nonexistent_spread", "Test")
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "nonexistent_spread" in str(e)
