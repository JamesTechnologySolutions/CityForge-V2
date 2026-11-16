"""Tests for the acceleration layer (C++ bindings with Python fallback)."""

from cityforge import accel
from cityforge import content as C


def test_accel_covers_all_paths() -> None:
    assert hasattr(accel, "compute_congestion")
    assert hasattr(accel, "advance_cars")


def test_compute_congestion_fallback() -> None:
    roads = [0] * 12
    roads[0] = 1
    loads = [0.0] * 12
    value = accel.compute_congestion(loads, roads, capacity=14.0)
    assert 0.0 <= value <= 1.0
