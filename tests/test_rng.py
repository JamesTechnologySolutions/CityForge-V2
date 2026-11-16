"""Tests for the deterministic RNG."""

from cityforge.rng import Lcg


def test_lcg_is_deterministic() -> None:
    assert Lcg(1234).next_float() == Lcg(1234).next_float()


def test_lcg_stays_in_unit_range() -> None:
    rng = Lcg(7)
    for _ in range(100):
        assert 0.0 <= rng.next_float() < 1.0


def test_lcg_next_int() -> None:
    rng = Lcg(99)
    values = {rng.next_int(10) for _ in range(200)}
    assert values.issubset(set(range(10)))
