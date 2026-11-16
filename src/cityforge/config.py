"""Runtime configuration for a Cityforge game session."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final

DEFAULT_SAVE_PATH: Final[str] = "cityforge-save.json"
DEFAULT_LOG_FILE: Final[str] = "cityforge.log"


@dataclass(frozen=True)
class GameConfig:
    """Immutable game tuning knobs.

    The defaults mirror the original CityForge-V2 prototype; every value is
    exposed so future features (season length, disaster intensity, traffic
    density, ...) can be tuned without touching simulation code.
    """

    map_size: int = 56
    tile_width: int = 64
    tile_height: int = 32
    initial_money: int = 15000
    start_tax_rate: float = 9.0
    tax_min: float = 0.0
    tax_max: float = 20.0
    autosave_day_interval: int = 30
    save_path: str = DEFAULT_SAVE_PATH
    log_level: int = 20  # logging.INFO
    log_file: str | None = DEFAULT_LOG_FILE
    speed_steps_ms: tuple[int, ...] = (0, 1000, 450, 150)  # pause, 1x, 2x, 3x
    start_happiness: float = 50.0
    initial_population: int = 0
    initial_jobs: int = 0

    @classmethod
    def from_file(cls, path: str | os.PathLike[str]) -> GameConfig:
        """Build a config from a JSON file (all fields are optional)."""
        import json

        raw: dict[str, object] = {}
        try:
            raw = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        fields = {f.name for f in cls.__dataclass_fields__.values()}
        values: dict[str, object] = {}
        for key, value in raw.items():
            if key in fields:
                values[key] = value
        return cls(**values)  # type: ignore[arg-type]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON friendly dict of the active config."""
        return {
            "map_size": self.map_size,
            "tile_width": self.tile_width,
            "tile_height": self.tile_height,
            "initial_money": self.initial_money,
            "start_tax_rate": self.start_tax_rate,
            "tax_min": self.tax_min,
            "tax_max": self.tax_max,
            "autosave_day_interval": self.autosave_day_interval,
            "save_path": self.save_path,
            "speed_steps_ms": list(self.speed_steps_ms),
        }


def user_save_path(config: GameConfig) -> Path:
    """Resolve the save file location (env override -> config -> default)."""
    override = os.environ.get("CITYFORGE_SAVE")
    base = Path(override) if override else Path(config.save_path)
    return base


def user_log_path(config: GameConfig) -> Path:
    """Resolve the log file location (env override -> config -> default)."""
    override = os.environ.get("CITYFORGE_LOG")
    return Path(override) if override else Path(config.log_file or DEFAULT_LOG_FILE)
