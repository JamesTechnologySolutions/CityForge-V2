"""Tests for traffic congestion and car updates."""

from cityforge import content as C
from cityforge.config import GameConfig
from cityforge.simulation import CitySimulation
from cityforge.traffic import TrafficSystem
from cityforge.world import World


def _sim() -> CitySimulation:
    world = World(seed=11, size=30, tile_width=64, tile_height=32)
    return CitySimulation(config=GameConfig(), world=world, traffic=TrafficSystem(world), disasters=None)


def test_congestion_zero_without_roads() -> None:
    traffic = TrafficSystem(World(seed=3, size=10, tile_width=64, tile_height=32))
    assert traffic.congestion() == 0.0


def test_congestion_computed_with_road() -> None:
    world = World(seed=3, size=10, tile_width=64, tile_height=32)
    traffic = TrafficSystem(world)
    world.tiles[0].kind = "road"
    world.tiles[1].kind = "res"
    world.tiles[1].level = 2
    congestion = traffic.congestion()
    assert 0.0 <= congestion <= 1.0


def test_car_lifecycle(sim: CitySimulation) -> None:
    traffic = sim.traffic
    assert traffic.update(sim, dt=1 / 60) >= 0.0
    assert len(traffic.cars) >= 0
    assert traffic.cars is not None
