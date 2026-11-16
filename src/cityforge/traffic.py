"""Live traffic: car agents, congestion and road load computation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from cityforge import content as C
from cityforge.model import Car, Tile
from cityforge.rng import Lcg
from cityforge.world import World

if TYPE_CHECKING:  # pragma: no cover
    from cityforge.simulation import CitySimulation

DIRECTIONS: tuple[tuple[int, int], ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))


class TrafficSystem:
    """Owns the car agents and computes road congestion for a city."""

    def __init__(self, world: World) -> None:
        self.world = world
        self.cars: list[Car] = []

    # ------------------------------------------------------------------ congestion
    def congestion(self) -> float:
        """Average capped congestion across all road tiles (0.0 - 1.0)."""
        roads = [tile for tile in self.world.tiles if tile.kind == "road"]
        if not roads:
            return 0.0
        congestion_sum = 0.0
        for road in roads:
            nearby_roads = self._nearby_roads(road.x, road.y, radius=2)
            load = 0.0
            for candidate in nearby_roads:
                if candidate.kind in ("res", "com", "ind") and candidate.level > 0:
                    load += candidate.level * C.TOOLS[candidate.kind].traffic_load_per_level / len(nearby_roads)
            road.traffic_load = load
            congestion_sum += min(1.0, load / C.VELOCITY_CONGESTION_THRESHOLD)
        return congestion_sum / len(roads)

    def _nearby_roads(self, x: int, y: int, radius: int) -> list[Tile]:
        """Road tiles within Chebyshev distance ``radius`` (including self)."""
        found: list[Tile] = []
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                tile = self.world.tile_at(x + dx, y + dy)
                if tile is not None and tile.kind == "road":
                    found.append(tile)
        return found

    # ------------------------------------------------------------------ cars
    def update(self, sim: "CitySimulation", dt: float = 1.0 / 60.0) -> float:
        """Advance the traffic simulation by ``dt`` seconds. Returns congestion."""
        want = min(C.CAR_TARGET_MAX, int(sim.pop / C.CAR_TARGET_PER_RESIDENT + sim.jobs / C.CAR_TARGET_PER_JOB))
        while len(self.cars) < want:
            if not self.spawn_car():
                break
        if len(self.cars) > want:
            del self.cars[want:]

        speed = C.CAR_SPEED_PER_SPEED_STEP[sim.speed] * dt
        for car in reversed(self.cars):
            current = sim.world.tile_at(car.x, car.y)
            if current is None or current.kind != "road":
                self.cars.remove(car)
                continue
            car.p += speed * C.VELOCITY_PER_SPEED_STEP * (
                1 - min(1.0, current.traffic_load / C.VELOCITY_CONGESTION_THRESHOLD) * C.VELOCITY_CONGESTION_DECAY
            )
            while car.p >= 1.0:
                car.p -= 1.0
                car.px = car.x
                car.py = car.y
                if car.nx >= 0:
                    nxt = sim.world.tile_at(car.nx, car.ny)
                    if nxt is not None and nxt.kind == "road":
                        car.x = car.nx
                        car.y = car.ny
                if not self.next_hop(car):
                    car.p = 0.0
                    car.nx = -1
                    break
            if car.nx < 0 and not self.next_hop(car):
                car.p = 0.0
        return self.congestion()

    # ------------------------------------------------------------------ internals
    def spawn_car(self) -> bool:
        """Spawn a car on a random road tile."""
        roads = [tile for tile in self.world.tiles if tile.kind == "road"]
        if not roads:
            return False
        tile = roads[int(Lcg(20240617).next_float() * len(roads))]
        self.cars.append(
            Car(
                x=tile.x,
                y=tile.y,
                nx=-1,
                ny=0,
                p=1.0,
                px=-1,
                py=-1,
                color=C.CAR_COLORS[int(Lcg(424242).next_float() * len(C.CAR_COLORS))],
            )
        )
        return True

    def next_hop(self, car: Car) -> bool:
        """Pick the next road neighbour for ``car``."""
        options = [
            (car.x + dx, car.y + dy)
            for dx, dy in DIRECTIONS
            if (tile := self.world.tile_at(car.x + dx, car.y + dy)) is not None and tile.kind == "road"
        ]
        if not options:
            return False
        forward = [opt for opt in options if opt != (car.px, car.py)]
        pool = forward if forward else options
        nx, ny = pool[int(Lcg(99).next_float() * len(pool))]
        car.nx = nx
        car.ny = ny
        car.p = 0.0
        return True
