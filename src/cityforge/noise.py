"""Tiny value-noise terrain generator used for the isometric map."""

from __future__ import annotations

from cityforge.rng import Lcg


def _smoothstep(t: float) -> float:
    """Cubic smoothstep ``t * t * (3 - 2 * t)``."""
    return t * t * (3.0 - 2.0 * t)


class ValueNoise:
    """Bilinear value-noise over an integer grid.

    This is a faithful port of the noise used by the original JavaScript
    prototype (smoothstep interpolation of a coarse grid generated from a
    deterministic linear congruential sequence).
    """

    def __init__(self, seed: int = 0, grid: int = 8) -> None:
        self._rng = Lcg(seed)
        self._grid = grid
        self._values: list[list[float]] = [
            [self._rng.next_float() for _ in range(grid + 2)] for _ in range(grid + 2)
        ]

    def noise(self, x: float, y: float, world_size: int) -> float:
        """Return a noise sample in ``[0.0, 1.0]`` for world coordinates."""
        g = self._grid
        fx = x / world_size * g
        fy = y / world_size * g
        ix = int(fx)
        iy = int(fy)
        tx = _smoothstep(fx - ix)
        ty = _smoothstep(fy - iy)
        row = self._values
        a = row[iy][ix]
        b = row[iy][ix + 1]
        c = row[iy + 1][ix]
        d = row[iy + 1][ix + 1]
        return a + (b - a) * tx + (c - a) * ty + (a - b - c + d) * tx * ty
