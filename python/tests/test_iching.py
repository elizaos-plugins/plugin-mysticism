"""Smoke tests for the I Ching engine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elizaos_plugin_mysticism.engines.iching import (
    IChingEngine,
    binary_to_hexagram_number,
    cast_hexagram,
    get_hexagram,
    get_lower_trigram,
    get_trigram,
    get_upper_trigram,
)
from elizaos_plugin_mysticism.types import FeedbackEntry


# ------------------------------------------------------------------
# Casting basics
# ------------------------------------------------------------------


def test_cast_hexagram_produces_valid_lines():
    result = cast_hexagram()
    assert len(result.lines) == 6
    for line in result.lines:
        assert line in (6, 7, 8, 9)


def test_cast_hexagram_binary_length():
    result = cast_hexagram()
    assert len(result.binary) == 6
    for ch in result.binary:
        assert ch in ("0", "1")


def test_cast_hexagram_number_range():
    result = cast_hexagram()
    assert 1 <= result.hexagramNumber <= 64


def test_transformed_hexagram_only_with_changing_lines():
    # Run several casts; when there are no changing lines, transformed should be None
    for _ in range(100):
        result = cast_hexagram()
        if not result.changingLines:
            assert result.transformedHexagramNumber is None
            assert result.transformedBinary is None
        else:
            assert result.transformedHexagramNumber is not None
            assert result.transformedBinary is not None


# ------------------------------------------------------------------
# Hexagram / trigram lookups
# ------------------------------------------------------------------


def test_all_64_hexagrams_accessible():
    for n in range(1, 65):
        h = get_hexagram(n)
        assert h.number == n
        assert len(h.binary) == 6


def test_all_8_trigrams_accessible():
    for n in range(1, 9):
        t = get_trigram(n)
        assert t.number == n
        assert len(t.binary) == 3


def test_binary_to_hexagram_creative():
    # Hexagram 1 (Qian / The Creative) = 111111
    num = binary_to_hexagram_number("111111")
    assert num == 1


def test_binary_to_hexagram_receptive():
    # Hexagram 2 (Kun / The Receptive) = 000000
    num = binary_to_hexagram_number("000000")
    assert num == 2


def test_trigram_from_hexagram():
    h = get_hexagram(1)  # The Creative: both trigrams are Qian (1)
    upper = get_upper_trigram(h)
    lower = get_lower_trigram(h)
    assert upper.number == 1
    assert lower.number == 1


def test_invalid_hexagram_raises():
    try:
        get_hexagram(0)
        assert False, "Expected ValueError"
    except ValueError:
        pass

    try:
        get_hexagram(65)
        assert False, "Expected ValueError"
    except ValueError:
        pass


# ------------------------------------------------------------------
# Engine lifecycle
# ------------------------------------------------------------------


def test_engine_start_reading():
    engine = IChingEngine()
    state = engine.start_reading("What is the way forward?")
    assert state.question == "What is the way forward?"
    assert 1 <= state.hexagram.number <= 64
    assert state.revealedLines == 0


def test_engine_reveal_cycle():
    engine = IChingEngine()
    state = engine.start_reading("Test question")

    # Reveal all changing lines
    count = 0
    while True:
        reveal = engine.get_next_reveal(state)
        if reveal is None:
            break
        feedback = FeedbackEntry(
            element=f"line_{reveal['linePosition']}",
            userText="Noted",
            timestamp=0,
        )
        state = engine.record_feedback(state, feedback)
        count += 1

    assert engine.is_complete(state)
    assert count == len(state.castResult.changingLines)


def test_engine_synthesis():
    engine = IChingEngine()
    state = engine.start_reading("Seeking clarity")

    # Complete all reveals
    while engine.get_next_reveal(state) is not None:
        reveal = engine.get_next_reveal(state)
        feedback = FeedbackEntry(element="line", userText="Ok", timestamp=0)
        state = engine.record_feedback(state, feedback)

    synthesis = engine.get_synthesis(state)
    assert "hexagram" in synthesis
    assert "question" in synthesis


def test_engine_casting_summary():
    engine = IChingEngine()
    state = engine.start_reading("General inquiry")
    summary = engine.get_casting_summary(state)
    assert "Hexagram" in summary
    assert "Upper:" in summary
    assert "Lower:" in summary
