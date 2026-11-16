"""Tests for the city simulation."""

from cityforge import content as C
from cityforge.config import GameConfig
from cityforge.model import Tile
from cityforge.simulation import CitySimulation
from cityforge.traffic import TrafficSystem
from cityforge.world import World


def _make_sim(config: GameConfig | None = None, world: World | None = None) -> CitySimulation:
    world = world or World(seed=20240617, size=56, tile_width=64, tile_height=32)
    return CitySimulation(config=config or GameConfig(), world=world, traffic=TrafficSystem(world), disasters=None)


def test_new_city_starts_broke_and_empty(sim) -> None:
    assert sim.money == 15000
    assert sim.day == 0
    assert sim.pop == 0
    assert sim.happy == 50
    assert sim.rank == 0


def test_tick_advances_day_and_budget(sim) -> None:
    before_money = sim.money
    sim.tick()
    assert sim.day == 1
    assert sim.exp >= 0
    assert sim.inc >= 0
    assert sim.money == before_money + sim.inc - sim.exp


def test_demand_keys_present(sim) -> None:
    sim.tick()
    assert set(sim.dem) == {"r", "c", "i"}


def test_build_road_then_zone_grows_needs_power(sim) -> None:
    world = World(seed=7, size=20, tile_width=64, tile_height=32)
    sim = CitySimulation(config=GameConfig(), world=world, traffic=TrafficSystem(world), disasters=None)
    world.tiles[0].kind = "road"
    world.tiles[1].kind = "road"
    world.tiles[2].kind = "res"
    sim.tick()
    assert world.tiles[2].road is True
    assert world.tiles[2].powered is False
    assert world.tiles[2].level == 0


def test_residential_happiness_with_coverage(sim) -> None:
    world = World(seed=7, size=20, tile_width=64, tile_height=32)
    sim = CitySimulation(config=GameConfig(), world=world, traffic=TrafficSystem(world), disasters=None)
    target = None
    for tile in world.tiles:
        if not tile.water and tile.kind is None:
            target = tile
            break
    assert target is not None
    target.kind = "res"
    target.level = 2
    world.tiles[1].kind = "road"
    sim.coverage = sim.world.cover()
    sim.coverage["power"] = [True] * len(sim.world.tiles)
    sim.coverage["water"] = [True] * len(sim.world.tiles)
    sim.tick()
    assert target.happiness > 0
    assert 0 <= target.happiness <= 100


def test_disaster_system_runs(sim) -> None:
    from cityforge.disasters import DisasterSystem

    world = World(seed=5, size=20, tile_width=64, tile_height=32)
    sim = CitySimulation(config=GameConfig(), world=world, traffic=TrafficSystem(world), disasters=None)
    sim.world.tiles[0].kind = "res"
    sim.world.tiles[0].level = 1
    sim.disasters = DisasterSystem(sim.world)
    assert sim.disasters.start_fire(sim) is True
    assert any(tile.fire > 0 for tile in sim.world.tiles)
    assert sim.disasters.quake(sim) >= 0
    assert sim.disasters.tornado(sim) >= 0
