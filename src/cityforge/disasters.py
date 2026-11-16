"""Disaster system: fire spread, earthquake and tornado."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from cityforge import content as C
from cityforge.rng import Lcg

if TYPE_CHECKING:  # pragma: no cover
    from cityforge.simulation import CitySimulation


class DisasterSystem:
    """Runs random and manual disasters against the world."""

    def __init__(self, world) -> None:
        self.world = world
        self.enabled: bool = True
        self.shake: float = 0.0

    # ------------------------------------------------------------------ tick
    def run(self, sim: "CitySimulation") -> None:
        """Spread fires, then roll for a new random disaster."""
        rng = Lcg(7777)
        fire_coverage = sim.coverage.get("fire")
        for tile in self.world.tiles:
            if not tile.fire:
                continue
            index = self.world.index(tile.x, tile.y)
            covered = bool(fire_coverage[index]) if fire_coverage is not None else False
            if covered and rng.next_float() < C.FIRE_EXTINGUISH_CHANCE:
                tile.fire = 0
                if tile.level > 0:
                    tile.level -= 1
                continue
            for dy in range(-C.FIRE_TILE_RADIUS, C.FIRE_TILE_RADIUS + 1):
                for dx in range(-C.FIRE_TILE_RADIUS, C.FIRE_TILE_RADIUS + 1):
                    neighbour = self.world.tile_at(tile.x + dx, tile.y + dy)
                    if neighbour is None or not neighbour.kind or neighbour.kind == "road" or neighbour.fire:
                        continue
                    spread = C.FIRE_SPREAD_INFERNO if abs(dx) <= 1 and abs(dy) <= 1 else C.FIRE_SPREAD_BASE
                    if covered:
                        spread *= C.FIRE_INFERNO_COVERAGE_FACTOR
                    if rng.next_float() < spread:
                        neighbour.fire = C.FIRE_TICKS
            tile.fire -= 1
            if tile.fire <= 0:
                tile.kind = None
                tile.level = 0
                tile.fire = 0

        if not self.enabled or sim.pop < 40:
            return
        roll = Lcg(31337).next_float()
        if roll < C.DISASTER_FIRE_CHANCE:
            self.start_fire(sim)
        elif roll < C.DISASTER_FIRE_CHANCE + C.DISASTER_QUAKE_CHANCE:
            self.quake(sim)
        elif roll < C.DISASTER_FIRE_CHANCE + C.DISASTER_QUAKE_CHANCE + C.DISASTER_TORNADO_CHANCE:
            self.tornado(sim)

    # ------------------------------------------------------------------ disasters
    def start_fire(self, sim: "CitySimulation") -> bool:
        """Ignite a random fire at a non-road tile. Returns success flag."""
        candidates = [tile for tile in self.world.tiles if tile.kind and tile.kind != "road"]
        if not candidates:
            return False
        tile = candidates[int(Lcg(5150).next_float() * len(candidates))]
        tile.fire = C.FIRE_TICKS
        return True

    def quake(self, sim: "CitySimulation") -> int:
        """Shake the city; returns number of damaged buildings."""
        self.shake = 14.0
        damaged = 0
        for tile in self.world.tiles:
            if not tile.kind or tile.kind == "road":
                continue
            is_zone = len(tile.kind) == 3
            if Lcg(808).next_float() < (C.EARTHQUAKE_ZONE_DAMAGE_CHANCE if is_zone else C.EARTHQUAKE_BUILDING_DAMAGE_CHANCE):
                if is_zone and tile.level > 1:
                    tile.level -= 1
                else:
                    tile.kind = None
                    tile.level = 0
                    tile.fire = 0
                damaged += 1
        return damaged

    def tornado(self, sim: "CitySimulation") -> int:
        """Drop a tornado; returns number of destroyed buildings."""
        destroyed = 0
        x = int(Lcg(606).next_float() * self.world.size)
        y = int(Lcg(707).next_float() * self.world.size)
        for _ in range(C.TORNADO_HITS):
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    tile = self.world.tile_at(x + dx, y + dy)
                    if tile is None or not tile.kind or tile.kind == "road":
                        continue
                    if Lcg(909).next_float() < 0.6:
                        tile.kind = None
                        tile.level = 0
                        tile.fire = 0
                        destroyed += 1
            x += int(Lcg(111).next_float() * 3)
            y += int(Lcg(222).next_float() * 3) - 1
        return destroyed

    def trigger_random(self, sim: "CitySimulation") -> Optional[str]:
        """Manually trigger a random disaster. Returns the kind or ``None``."""
        if not any(tile.kind and tile.kind != "road" for tile in self.world.tiles):
            return None
        roll = Lcg(1212).next_float()
        if roll < C.DISASTER_FIRE_CHANCE:
            self.start_fire(sim)
            return "fire"
        if roll < C.DISASTER_FIRE_CHANCE + C.DISASTER_QUAKE_CHANCE:
            self.quake(sim)
            return "quake"
        self.tornado(sim)
        return "tornado"
