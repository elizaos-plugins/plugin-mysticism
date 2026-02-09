"""Python dataclass mirrors of the TypeScript types for plugin-mysticism."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

@dataclass
class FeedbackEntry:
    element: str
    userText: str
    timestamp: float


ReadingPhase = Literal["intake", "casting", "interpretation", "synthesis", "closing"]
ReadingSystem = Literal["tarot", "iching", "astrology"]


# ---------------------------------------------------------------------------
# Tarot
# ---------------------------------------------------------------------------

@dataclass
class TarotCard:
    id: str
    name: str
    number: int
    arcana: Literal["major", "minor"]
    suit: Optional[Literal["wands", "cups", "swords", "pentacles"]]
    keywords_upright: list[str]
    keywords_reversed: list[str]
    meaning_upright: str
    meaning_reversed: str
    description: str
    element: str
    planet: Optional[str]
    zodiac: Optional[str]
    numerology: int


@dataclass
class DrawnCard:
    card: TarotCard
    reversed: bool
    positionIndex: int


@dataclass
class SpreadPosition:
    index: int
    name: str
    description: str


@dataclass
class SpreadDefinition:
    id: str
    name: str
    description: str
    positions: list[SpreadPosition]
    cardCount: int


@dataclass
class TarotReadingState:
    spread: SpreadDefinition
    drawnCards: list[DrawnCard]
    revealedIndex: int
    question: str
    userFeedback: list[FeedbackEntry] = field(default_factory=list)


# ---------------------------------------------------------------------------
# I Ching
# ---------------------------------------------------------------------------

@dataclass
class Trigram:
    number: int
    name: str
    englishName: str
    character: str
    binary: str
    lines: list[int]
    attribute: str
    image: str
    family: str
    element: str
    direction: str
    bodyPart: str


@dataclass
class HexagramLine:
    position: int
    text: str
    meaning: str


@dataclass
class Hexagram:
    number: int
    name: str
    englishName: str
    character: str
    binary: str
    topTrigram: int
    bottomTrigram: int
    judgment: str
    image: str
    lines: list[HexagramLine]
    keywords: list[str]
    description: str


@dataclass
class CastResult:
    lines: list[int]
    changingLines: list[int]
    hexagramNumber: int
    transformedHexagramNumber: Optional[int]
    binary: str
    transformedBinary: Optional[str]


@dataclass
class IChingReadingState:
    question: str
    castResult: CastResult
    hexagram: Hexagram
    transformedHexagram: Optional[Hexagram]
    revealedLines: int
    userFeedback: list[FeedbackEntry] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Astrology
# ---------------------------------------------------------------------------

@dataclass
class BirthData:
    year: int
    month: int
    day: Optional[int] = None
    hour: Optional[int] = None
    minute: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[float] = None


@dataclass
class PlanetPosition:
    planet: str
    sign: str
    degrees: float
    totalDegrees: float
    house: int
    retrograde: bool


@dataclass
class SignPosition:
    sign: str
    degrees: float
    totalDegrees: float


@dataclass
class ChartAspect:
    planet1: str
    planet2: str
    aspectName: str
    aspectSymbol: str
    exactDegrees: float
    actualDegrees: float
    orb: float
    nature: Literal["harmonious", "challenging", "neutral"]


@dataclass
class NatalChart:
    sun: PlanetPosition
    moon: PlanetPosition
    mercury: PlanetPosition
    venus: PlanetPosition
    mars: PlanetPosition
    jupiter: PlanetPosition
    saturn: PlanetPosition
    uranus: PlanetPosition
    neptune: PlanetPosition
    pluto: PlanetPosition
    ascendant: SignPosition
    midheaven: SignPosition
    aspects: list[ChartAspect]
    houseCusps: list[float]


@dataclass
class AstrologyReadingState:
    birthData: BirthData
    chart: NatalChart
    revealedPlanets: list[str] = field(default_factory=list)
    revealedHouses: list[str] = field(default_factory=list)
    userFeedback: list[FeedbackEntry] = field(default_factory=list)
