"""City save / load persistence (JSON file storage)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from cityforge.model import Tile

if TYPE_CHECKING:  # pragma: no cover
    from cityforge.simulation import CitySimulation

SAVE_VERSION: int = 1


def build_save(sim: "CitySimulation") -> dict[str, Any]:
    """Serialise the mutable simulation state into a JSON friendly dict."""
    return {
        "version": SAVE_VERSION,
        "seed": sim.world.seed,
        "money": sim.money,
        "day": sim.day,
        "tax": sim.tax,
        "speed": sim.speed,
        "name": sim.name,
        "pop": sim.pop,
        "jobs": sim.jobs,
        "happy": sim.happy,
        "dem": dict(sim.dem),
        "inc": sim.inc,
        "exp": sim.exp,
        "rank": sim.rank,
        "t": [
            [int(tile.water), tile.kind, int(tile.level), int(tile.tree)]
            for tile in sim.world.tiles
        ],
    }


def apply_save(sim: "CitySimulation", data: dict[str, Any]) -> bool:
    """Restore simulation state from a previously serialised save dict."""
    try:
        tiles_data = data["t"]
        tiles: list[Tile] = []
        for position, entry in enumerate(tiles_data):
            water = bool(entry[0])
            kind = entry[1]
            level = int(entry[2])
            tree = bool(entry[3])
            index = position
            tiles.append(
                Tile(
                    x=index % sim.world.size,
                    y=index // sim.world.size,
                    water=water,
                    kind=kind,
                    level=level,
                    tree=tree,
                )
            )
        sim.world.tiles = tiles
        sim.money = float(data.get("money", sim.money))
        sim.day = int(data.get("day", sim.day))
        sim.tax = float(data.get("tax", sim.tax))
        sim.speed = int(data.get("speed", sim.speed))
        sim.name = str(data.get("name", sim.name))
        sim.pop = float(data.get("pop", sim.pop))
        sim.jobs = float(data.get("jobs", sim.jobs))
        sim.happy = float(data.get("happy", sim.happy))
        sim.dem = dict(data.get("dem") or {"r": 1.0, "c": 1.0, "i": 1.0})
        sim.inc = float(data.get("inc", sim.inc))
        sim.exp = float(data.get("exp", sim.exp))
        sim.rank = int(data.get("rank", sim.rank))
        return True
    except (KeyError, IndexError, TypeError, ValueError):
        return False


def save_game(sim: "CitySimulation", path: str) -> bool:
    """Write the current city to ``path`` as JSON."""
    Path(path).write_text(json.dumps(build_save(sim), separators=(",", ":")), encoding="utf-8")
    return True


def load_game(sim: "CitySimulation", path: str) -> bool:
    """Read a city from ``path``. Returns True when a city was loaded."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return apply_save(sim, data)
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        return False
