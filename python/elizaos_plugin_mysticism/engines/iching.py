"""I Ching divination engine — Python port of typescript/src/engines/iching/.

Uses the three-coin method with cryptographic randomness (``secrets``).
All reading state is external (``IChingReadingState``); the engine is stateless.
"""

from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Optional

from elizaos_plugin_mysticism.types import (
    CastResult,
    FeedbackEntry,
    Hexagram,
    HexagramLine,
    IChingReadingState,
    Trigram,
)

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"

_trigrams_cache: Optional[list[Trigram]] = None
_hexagrams_cache: Optional[list[Hexagram]] = None


def _load_trigrams() -> list[Trigram]:
    global _trigrams_cache
    if _trigrams_cache is not None:
        return _trigrams_cache
    path = _DATA_DIR / "iching" / "trigrams.json"
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    _trigrams_cache = [Trigram(**t) for t in raw]
    return _trigrams_cache


def _load_hexagrams() -> list[Hexagram]:
    global _hexagrams_cache
    if _hexagrams_cache is not None:
        return _hexagrams_cache
    path = _DATA_DIR / "iching" / "hexagrams.json"
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    result: list[Hexagram] = []
    for h in raw:
        lines = [HexagramLine(**ln) for ln in h["lines"]]
        result.append(
            Hexagram(
                number=h["number"],
                name=h["name"],
                englishName=h["englishName"],
                character=h["character"],
                binary=h["binary"],
                topTrigram=h["topTrigram"],
                bottomTrigram=h["bottomTrigram"],
                judgment=h["judgment"],
                image=h["image"],
                lines=lines,
                keywords=h["keywords"],
                description=h["description"],
            )
        )
    _hexagrams_cache = result
    return _hexagrams_cache


# ---------------------------------------------------------------------------
# Lookup maps (lazily built)
# ---------------------------------------------------------------------------

_trigram_by_number: Optional[dict[int, Trigram]] = None
_hexagram_by_number: Optional[dict[int, Hexagram]] = None
_binary_to_number: Optional[dict[str, int]] = None


def _build_lookups() -> None:
    global _trigram_by_number, _hexagram_by_number, _binary_to_number
    if _trigram_by_number is not None:
        return
    trigs = _load_trigrams()
    hexes = _load_hexagrams()
    _trigram_by_number = {t.number: t for t in trigs}
    _hexagram_by_number = {h.number: h for h in hexes}
    _binary_to_number = {h.binary: h.number for h in hexes}


# ---------------------------------------------------------------------------
# Coin toss helpers
# ---------------------------------------------------------------------------


def _flip_coin() -> bool:
    """Return True (heads) or False (tails) with cryptographic randomness."""
    return secrets.randbelow(2) >= 1


def _cast_line() -> tuple[int, bool]:
    """Cast a single I Ching line using the three-coin method.

    Heads = 3, Tails = 2.
    Sum determines line type:
      6 (2+2+2) = Old Yin   (changing broken line)
      7 (2+2+3) = Young Yang (stable solid line)
      8 (2+3+3) = Young Yin  (stable broken line)
      9 (3+3+3) = Old Yang   (changing solid line)

    Returns:
        (value, changing) tuple.
    """
    coin1 = 3 if _flip_coin() else 2
    coin2 = 3 if _flip_coin() else 2
    coin3 = 3 if _flip_coin() else 2
    value = coin1 + coin2 + coin3
    return value, (value == 6 or value == 9)


def _line_value_to_binary(value: int) -> int:
    """7 and 9 are yang (solid) -> 1; 6 and 8 are yin (broken) -> 0."""
    return 1 if value in (7, 9) else 0


def _line_value_to_transformed_binary(value: int) -> int:
    """Transform changing lines: Old Yin (6) -> Yang (1), Old Yang (9) -> Yin (0)."""
    if value == 6:
        return 1  # Old Yin -> Yang
    if value == 9:
        return 0  # Old Yang -> Yin
    return _line_value_to_binary(value)


# ---------------------------------------------------------------------------
# Public casting functions
# ---------------------------------------------------------------------------


def cast_hexagram() -> CastResult:
    """Cast a full hexagram (6 lines, bottom to top)."""
    _build_lookups()

    cast_lines: list[tuple[int, bool]] = []
    for _ in range(6):
        cast_lines.append(_cast_line())

    lines = [cl[0] for cl in cast_lines]
    changing_lines = [i + 1 for i, cl in enumerate(cast_lines) if cl[1]]

    # Build binary string (bottom to top = left to right)
    binary = "".join(str(_line_value_to_binary(cl[0])) for cl in cast_lines)
    hexagram_number = binary_to_hexagram_number(binary)

    transformed_hexagram_number: Optional[int] = None
    transformed_binary: Optional[str] = None

    if changing_lines:
        transformed_binary = "".join(
            str(_line_value_to_transformed_binary(cl[0])) for cl in cast_lines
        )
        transformed_hexagram_number = binary_to_hexagram_number(transformed_binary)

    return CastResult(
        lines=lines,
        changingLines=changing_lines,
        hexagramNumber=hexagram_number,
        transformedHexagramNumber=transformed_hexagram_number,
        binary=binary,
        transformedBinary=transformed_binary,
    )


def binary_to_hexagram_number(binary: str) -> int:
    """Look up hexagram number from its 6-digit binary representation."""
    _build_lookups()
    assert _binary_to_number is not None
    number = _binary_to_number.get(binary)
    if number is None:
        raise ValueError(f"Unknown hexagram binary pattern: {binary}")
    return number


def get_hexagram(number: int) -> Hexagram:
    """Look up a hexagram by its King Wen number (1-64)."""
    _build_lookups()
    assert _hexagram_by_number is not None
    hexagram = _hexagram_by_number.get(number)
    if hexagram is None:
        raise ValueError(f"Hexagram number {number} not found (valid range: 1-64)")
    return hexagram


def get_trigram(number: int) -> Trigram:
    """Look up a trigram by number (1-8)."""
    _build_lookups()
    assert _trigram_by_number is not None
    trigram = _trigram_by_number.get(number)
    if trigram is None:
        raise ValueError(f"Trigram number {number} not found (valid range: 1-8)")
    return trigram


def get_lower_trigram(hexagram: Hexagram) -> Trigram:
    return get_trigram(hexagram.bottomTrigram)


def get_upper_trigram(hexagram: Hexagram) -> Trigram:
    return get_trigram(hexagram.topTrigram)


# ---------------------------------------------------------------------------
# IChingEngine
# ---------------------------------------------------------------------------


class IChingEngine:
    """Stateless I Ching engine — all reading state lives in IChingReadingState."""

    def start_reading(self, question: str) -> IChingReadingState:
        cast_result = cast_hexagram()
        hexagram = get_hexagram(cast_result.hexagramNumber)

        transformed_hexagram: Optional[Hexagram] = None
        if cast_result.transformedHexagramNumber is not None:
            transformed_hexagram = get_hexagram(cast_result.transformedHexagramNumber)

        return IChingReadingState(
            question=question,
            castResult=cast_result,
            hexagram=hexagram,
            transformedHexagram=transformed_hexagram,
            revealedLines=0,
            userFeedback=[],
        )

    def get_next_reveal(
        self,
        state: IChingReadingState,
    ) -> Optional[dict]:
        """Return the next changing line to reveal, or None when done."""
        sorted_changing = sorted(state.castResult.changingLines)

        if state.revealedLines >= len(sorted_changing):
            return None

        line_position = sorted_changing[state.revealedLines]
        return {"linePosition": line_position}

    def record_feedback(
        self,
        state: IChingReadingState,
        feedback: FeedbackEntry,
    ) -> IChingReadingState:
        return IChingReadingState(
            question=state.question,
            castResult=state.castResult,
            hexagram=state.hexagram,
            transformedHexagram=state.transformedHexagram,
            revealedLines=state.revealedLines + 1,
            userFeedback=[*state.userFeedback, feedback],
        )

    def get_synthesis(self, state: IChingReadingState) -> dict:
        """Return a summary of the reading."""
        return {
            "hexagram": {
                "number": state.hexagram.number,
                "name": state.hexagram.name,
                "englishName": state.hexagram.englishName,
            },
            "transformedHexagram": (
                {
                    "number": state.transformedHexagram.number,
                    "name": state.transformedHexagram.name,
                    "englishName": state.transformedHexagram.englishName,
                }
                if state.transformedHexagram
                else None
            ),
            "changingLines": state.castResult.changingLines,
            "question": state.question,
            "feedback": [
                {"element": fb.element, "userText": fb.userText}
                for fb in state.userFeedback
            ],
        }

    def is_complete(self, state: IChingReadingState) -> bool:
        sorted_changing = sorted(state.castResult.changingLines)
        return state.revealedLines >= len(sorted_changing)

    def get_casting_summary(self, state: IChingReadingState) -> str:
        """Human-readable summary of the cast."""
        hexagram = state.hexagram
        cast_result = state.castResult
        transformed = state.transformedHexagram

        upper = get_upper_trigram(hexagram)
        lower = get_lower_trigram(hexagram)

        parts: list[str] = [
            f"{hexagram.character} Hexagram {hexagram.number}: "
            f"{hexagram.name} — {hexagram.englishName}",
            "",
            f"Upper: {upper.character} {upper.englishName} ({upper.image})",
            f"Lower: {lower.character} {lower.englishName} ({lower.image})",
        ]

        if cast_result.changingLines:
            lines_str = ", ".join(f"Line {l}" for l in cast_result.changingLines)
            parts.extend(["", f"Changing lines: {lines_str}"])
        else:
            parts.extend(["", "No changing lines — the reading is stable."])

        if transformed:
            parts.extend([
                "",
                f"Transforming to: {transformed.character} Hexagram "
                f"{transformed.number}: {transformed.name} — {transformed.englishName}",
            ])

        return "\n".join(parts)
