"""Tarot divination engine — Python port of typescript/src/engines/tarot/.

Uses Fisher-Yates shuffle with cryptographic randomness (``secrets``).
All reading state is external (``TarotReadingState``); the engine is stateless.
"""

from __future__ import annotations

import json
import secrets
from copy import deepcopy
from pathlib import Path
from typing import Optional

from elizaos_plugin_mysticism.types import (
    DrawnCard,
    FeedbackEntry,
    SpreadDefinition,
    SpreadPosition,
    TarotCard,
    TarotReadingState,
)

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"

_cards_cache: Optional[list[TarotCard]] = None
_spreads_cache: Optional[list[SpreadDefinition]] = None


def _load_cards() -> list[TarotCard]:
    global _cards_cache
    if _cards_cache is not None:
        return _cards_cache
    path = _DATA_DIR / "tarot" / "cards.json"
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    _cards_cache = [TarotCard(**card) for card in raw]
    return _cards_cache


def _load_spreads() -> list[SpreadDefinition]:
    global _spreads_cache
    if _spreads_cache is not None:
        return _spreads_cache
    path = _DATA_DIR / "tarot" / "spreads.json"
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    result: list[SpreadDefinition] = []
    for s in raw:
        positions = [SpreadPosition(**p) for p in s["positions"]]
        result.append(
            SpreadDefinition(
                id=s["id"],
                name=s["name"],
                description=s["description"],
                positions=positions,
                cardCount=s["cardCount"],
            )
        )
    _spreads_cache = result
    return _spreads_cache


# ---------------------------------------------------------------------------
# Deck operations
# ---------------------------------------------------------------------------


def create_deck() -> list[TarotCard]:
    """Return a fresh copy of the 78-card deck."""
    return list(_load_cards())


def shuffle_deck(cards: list[TarotCard]) -> list[TarotCard]:
    """Fisher-Yates shuffle using cryptographic randomness."""
    shuffled = list(cards)
    for i in range(len(shuffled) - 1, 0, -1):
        # Generate a random float in [0, 1) using 4 bytes of entropy
        rand_float = int.from_bytes(secrets.token_bytes(4), "big") / 0x100000000
        j = int(rand_float * (i + 1))
        shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    return shuffled


def draw_cards(
    deck: list[TarotCard],
    count: int,
    allow_reversals: bool = True,
) -> list[DrawnCard]:
    """Draw *count* cards from the top of the (pre-shuffled) deck."""
    if count > len(deck):
        raise ValueError(
            f"Cannot draw {count} cards from a deck of {len(deck)}"
        )
    if count < 0:
        raise ValueError("Card count must be non-negative")

    drawn: list[DrawnCard] = []
    for i in range(count):
        rand_float = int.from_bytes(secrets.token_bytes(4), "big") / 0x100000000
        reversed_ = allow_reversals and rand_float < 0.5
        drawn.append(DrawnCard(card=deck[i], reversed=reversed_, positionIndex=i))
    return drawn


# ---------------------------------------------------------------------------
# Spread helpers
# ---------------------------------------------------------------------------


def get_spread(spread_id: str) -> Optional[SpreadDefinition]:
    """Look up a spread by id."""
    for s in _load_spreads():
        if s.id == spread_id:
            return s
    return None


def get_all_spreads() -> list[SpreadDefinition]:
    """Return all available spread definitions."""
    return list(_load_spreads())


# ---------------------------------------------------------------------------
# TarotEngine
# ---------------------------------------------------------------------------


class TarotEngine:
    """Stateless tarot engine — all reading state lives in TarotReadingState."""

    def start_reading(
        self,
        spread_id: str,
        question: str,
        allow_reversals: bool = True,
    ) -> TarotReadingState:
        spread = get_spread(spread_id)
        if spread is None:
            available = ", ".join(f'"{s.id}"' for s in get_all_spreads())
            raise ValueError(
                f'Unknown spread "{spread_id}". Available spreads: {available}'
            )

        deck = shuffle_deck(create_deck())
        drawn = draw_cards(deck, spread.cardCount, allow_reversals)

        return TarotReadingState(
            spread=spread,
            question=question,
            drawnCards=drawn,
            revealedIndex=0,
            userFeedback=[],
        )

    def get_next_reveal(
        self,
        state: TarotReadingState,
    ) -> Optional[dict]:
        """Return the next card + position, or None if all revealed."""
        if state.revealedIndex >= len(state.drawnCards):
            return None

        card = state.drawnCards[state.revealedIndex]
        position = state.spread.positions[state.revealedIndex]
        return {"card": card, "position": position}

    def record_feedback(
        self,
        state: TarotReadingState,
        feedback: FeedbackEntry,
    ) -> TarotReadingState:
        if state.revealedIndex >= len(state.drawnCards):
            raise RuntimeError(
                "Cannot record feedback: all cards have already been revealed"
            )
        return TarotReadingState(
            spread=state.spread,
            question=state.question,
            drawnCards=state.drawnCards,
            revealedIndex=state.revealedIndex + 1,
            userFeedback=[*state.userFeedback, feedback],
        )

    def get_synthesis(self, state: TarotReadingState) -> dict:
        """Return a summary dict once all cards are revealed."""
        if state.revealedIndex < len(state.drawnCards):
            remaining = len(state.drawnCards) - state.revealedIndex
            raise RuntimeError(
                f"Cannot synthesize: {remaining} card(s) have not been revealed yet"
            )
        return {
            "spread": state.spread.name,
            "question": state.question,
            "cards": [
                {
                    "position": state.spread.positions[i].name,
                    "card": dc.card.name,
                    "reversed": dc.reversed,
                }
                for i, dc in enumerate(state.drawnCards)
            ],
            "feedback": [
                {"element": fb.element, "userText": fb.userText}
                for fb in state.userFeedback
            ],
        }

    def is_complete(self, state: TarotReadingState) -> bool:
        return state.revealedIndex >= len(state.drawnCards)
