"""Core data classes: tiles, traffic cars and disaster bookkeeping."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Tile:
    """A single isometric map tile.

    ``kind`` is the placeable object (``None`` for open land, ``"road"`` for
    roads, zone/service kinds for buildings).  ``level`` is the build level of
    zones and services (0 = not built, up to ``ToolDef.max_level``).

    Runtime-only flags are recomputed by the simulation each tick and are not
    part of the persisted save file.
    """

    x: int
    y: int
    water: bool = False
    kind: Optional[str] = None
    level: int = 0
    tree: bool = False
    fire: int = 0
    road: bool = False
    powered: bool = False
    water_supply: bool = False
    happiness: float = 0.0
    traffic_load: float = 0.0

    @property
    def is_land(self) -> bool:
        """True when the tile is buildable terrain (not water)."""
        return not self.water


@dataclass
class Car:
    """A traffic vehicle travelling along the road network."""

    x: int = -1
    y: int = -1
    nx: int = -1
    ny: int = -1
    p: float = 1.0
    px: int = -1
    py: int = -1
    color: str = "#e8e8e8"

    @property
    def position(self) -> tuple[int, int]:
        """Current tile coordinates (interpolated by the simulation)."""
        return (self.x, self.y)


@dataclass
class DisasterState:
    """Mutable state of the disaster system (world shaking, toggles)."""

    enabled: bool = True
    shake: float = 0.0
    last_kind: Optional[str] = None


@dataclass
class HudSnapshot:
    """Immutable-ish snapshot of the numbers shown in the HUD."""

    money: float = 0.0
    day: int = 0
    tax: float = 0.0
    speed: int = 1
    name: str = ""
    pop: float = 0.0
    jobs: float = 0.0
    happy: float = 0.0
    dem_residential: float = 1.0
    dem_commercial: float = 1.0
    dem_industrial: float = 1.0
    income: float = 0.0
    expense: float = 0.0
    net: float = 0.0
    rank: int = 0

    @property
    def rank_name(self) -> str:
        """Human readable rank name for the current rank index."""
        from cityforge.content import RANKS

        return RANKS[self.rank][1]

    @property
    def month_name(self) -> str:
        """Short month label for the current in-game day."""
        from cityforge.content import MONTHS

        return MONTHS[(self.day % 360) // 30]

    @property
    def year(self) -> int:
        """In-game year (1-based)."""
        return 1 + self.day // 360
