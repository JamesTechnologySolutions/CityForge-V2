"""Tests for the value noise generator."""

from cityforge.noise import ValueNoise


def test_noise_is_deterministic_and_bounded() -> None:
    a = ValueNoise(seed=42, grid=8)
    b = ValueNoise(seed=42, grid=8)
    samples = [a.noise(x * 0.7, y * 0.9, 56) for x, y in ((0, 0), (5, 7), (12, 3), (30, 30))]
    assert all(0.0 <= value <= 1.0 for value in samples)
    assert samples == [b.noise(x * 0.7, y * 0.9, 56) for x, y in ((0, 0), (5, 7), (12, 3), (30, 30))]


def test_noise_seeds_change_output() -> None:
    assert ValueNoise(seed=1, grid=8).noise(3, 4, 56) != ValueNoise(seed=2, grid=8).noise(3, 4, 56)
