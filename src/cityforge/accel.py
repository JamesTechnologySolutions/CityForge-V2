"""Python bindings to the C++ hot paths, with pure Python fallbacks."""

from __future__ import annotations

from typing import Any

from cityforge import content as C

try:  # pragma: no cover - depends on the compiled extension
    from cityforge_core import advance_cars as _cpp_advance_cars
    from cityforge_core import compute_congestion as _cpp_compute_congestion

    ACCELERATED: bool = True
except Exception:  # pragma: no cover - extension not built
    ACCELERATED = False
    _cpp_compute_congestion = None
    _cpp_advance_cars = None


def compute_congestion(loads: list[float], roads: list[int], capacity: float = C.VELOCITY_CONGESTION_THRESHOLD) -> float:
    """Average capped congestion over road tiles (0.0 - 1.0)."""
    if ACCELERATED and _cpp_compute_congestion is not None:
        return float(_cpp_compute_congestion(loads, roads, capacity))
    total = 0.0
    count = 0
    for load, is_road in zip(loads, roads):
        if not is_road:
            continue
        total += min(1.0, load / capacity)
        count += 1
    return total / count if count else 0.0


def advance_cars(cars: list[list[float]], roads: list[int], loads: list[float], size: int, dt: float, speed: float) -> list[list[float]]:
    """Advance traffic cars by ``dt`` seconds; returns the new car states.

    Each car is a flat list of seven numbers: ``x, y, nx, ny, p, px, py``.
    ``roads`` is a flat 0/1 occupancy mask of ``size * size`` entries and
    ``loads`` holds the traffic load per road tile.
    """
    if ACCELERATED and _cpp_advance_cars is not None:
        flat: list[float] = []
        for car in cars:
            flat.extend(float(value) for value in car[:7])
        out: list[float] = []
        _cpp_advance_cars(flat, roads, loads, size, dt, speed, out)
        return [out[index : index + 7] for index in range(0, len(out), 7)]

    new_cars: list[list[float]] = []
    for car in cars:
        x, y, nx, ny, p, px, py = (float(car[0]), float(car[1]), float(car[2]), float(car[3]), float(car[4]), float(car[5]), float(car[6]))
        road_id = int(y) * size + int(x)
        factor = 1.0
        if roads[road_id]:
            factor = 1.0 - min(1.0, loads[road_id] / C.VELOCITY_CONGESTION_THRESHOLD) * C.VELOCITY_CONGESTION_DECAY
        p += C.CAR_SPEED_PER_SPEED_STEP[int(speed)] * dt * C.VELOCITY_PER_SPEED_STEP * factor
        while p >= 1.0:
            p -= 1.0
            px = x
            py = y
            if nx >= 0 and roads[int(ny) * size + int(nx)]:
                x = nx
                y = ny
            hopped = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                next_x = int(x) + dx
                next_y = int(y) + dy
                next_id = next_y * size + next_x
                if 0 <= next_x < size and 0 <= next_y < size and roads[next_id]:
                    nx = next_x
                    ny = next_y
                    p = 0.0
                    hopped = True
                    break
            if not hopped:
                break
        new_cars.append([x, y, nx, ny, p, px, py])
    return new_cars
