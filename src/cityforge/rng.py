"""Deterministic pseudo random number generator (ported from the original)."""

from __future__ import annotations


class Lcg:
    """Linear congruential generator.

    The original CityForge-V2 prototype used a hand rolled 32 bit LCG::

        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        value = state / 4294967296

    Keeping the exact arithmetic means procedurally generated worlds stay
    byte-for-byte compatible with the JavaScript version.
    """

    __slots__ = ("_state",)

    def __init__(self, seed: int = 0) -> None:
        self._state = int(seed) & 0xFFFFFFFF

    @property
    def state(self) -> int:
        """Current internal state (debug/introspection helper)."""
        return self._state

    def next_float(self) -> float:
        """Return the next value in ``[0.0, 1.0)``."""
        self._state = (1664525 * self._state + 1013904223) & 0xFFFFFFFF
        return self._state / 4294967296.0

    def next_int(self, bound: int) -> int:
        """Return a random integer in ``[0, bound)``."""
        if bound <= 0:
            return 0
        return int(self.next_float() * bound)

    def seed_from_int(self, seed: int) -> None:
        """Reset the generator from an integer seed."""
        self._state = int(seed) & 0xFFFFFFFF
