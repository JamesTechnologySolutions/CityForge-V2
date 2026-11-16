"""The tile world: terrain generation, coverage grids and neighbour queries."""

from __future__ import annotations

import math
from typing import Optional

from cityforge.content import COVERAGE_CATEGORIES, TOOLS
from cityforge.model import Tile
from cityforge.noise import ValueNoise
from cityforge.rng import Lcg

DEFAULT_WORLD_SEED: int = 1337


class _TreeNoise:
    """Deterministic per-tile forest probability generator."""

    def __init__(self, seed: int) -> None:
        self._rng = Lcg(seed)

    def next_float(self) -> float:
        return self._rng.next_float()


class World:
    """A square isometric tile grid with terrain, coverage and queries."""

    def __init__(self, seed: int, size: int, tile_width: int, tile_height: int) -> None:
        self.seed = int(seed)
        self.size = int(size)
        self.tile_width = int(tile_width)
        self.tile_height = int(tile_height)
        self.tiles: list[Tile] = []
        self._noise = ValueNoise(seed=seed, grid=8)
        self._tree_noise = _TreeNoise(seed)
        self.generate()

    # ------------------------------------------------------------------ setup
    def generate(self) -> None:
        """Create a fresh random terrain (land / water / forest)."""
        size = self.size
        tiles: list[Tile] = []
        for y in range(size):
            for x in range(size):
                water = math.hypot(x - size / 2, y - size / 2) > 9 and self._noise.noise(x, y, size) >= 0.36
                tiles.append(Tile(x=x, y=y, water=water, tree=self._tree_noise.next_float() < 0.12))
        self.tiles = tiles

    # ------------------------------------------------------------------ index
    def index(self, x: int, y: int) -> int:
        """Flat row-major tile index."""
        return y * self.size + x

    def in_bounds(self, x: int, y: int) -> bool:
        """True when ``(x, y)`` is inside the map."""
        return 0 <= x < self.size and 0 <= y < self.size

    def tile_at(self, x: int, y: int) -> Optional[Tile]:
        """Return the tile at ``(x, y)`` or ``None`` when out of bounds."""
        if not self.in_bounds(x, y):
            return None
        return self.tiles[self.index(x, y)]

    # ------------------------------------------------------------------ coverage
    def cover(self) -> dict[str, list[bool]]:
        """Compute service coverage grids (Manhattan radii) for this map."""
        size = self.size
        grids: dict[str, list[bool]] = {
            category: [False] * (size * size)
            for category in COVERAGE_CATEGORIES
        }
        for tile in self.tiles:
            definition = TOOLS.get(tile.kind) if tile.kind is not None else None
            if definition is None or definition.coverage_radius <= 0:
                continue
            category = definition.coverage_category or tile.kind
            grid = grids.setdefault(category, [False] * (size * size))
            radius = definition.coverage_radius
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if abs(dx) + abs(dy) > radius:
                        continue
                    nx = tile.x + dx
                    ny = tile.y + dy
                    if self.in_bounds(nx, ny):
                        grid[ny * size + nx] = True
        return grids

    # ------------------------------------------------------------------ queries
    def near_road(self, x: int, y: int, radius: int = 2) -> bool:
        """True when a road exists within Chebyshev distance ``radius``."""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                tile = self.tile_at(x + dx, y + dy)
                if tile is not None and tile.kind == "road":
                    return True
        return False

    def near_industrial(self, x: int, y: int, radius: int = 4) -> bool:
        """True when an industrial building is under construction nearby."""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                tile = self.tile_at(x + dx, y + dy)
                if tile is not None and tile.kind == "ind" and tile.level > 0:
                    return True
        return False
