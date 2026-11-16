"""Tests for persistence save / load."""

import json

from cityforge.config import GameConfig
from cityforge.persistence import apply_save, build_save, load_game, save_game
from cityforge.simulation import CitySimulation
from cityforge.traffic import TrafficSystem
from cityforge.world import World


def _sim() -> CitySimulation:
    world = World(seed=77, size=12, tile_width=64, tile_height=32)
    return CitySimulation(config=GameConfig(), world=world, traffic=TrafficSystem(world), disasters=None)


def test_save_builds_expected_shape(sim: CitySimulation) -> None:
    save = build_save(sim)
    assert save["version"] == 1
    assert save["seed"] == sim.world.seed
    assert len(save["t"]) == sim.world.size * sim.world.size
    assert save["t"][0][0] in (0, 1)
    assert save["t"][0][1] is None or isinstance(save["t"][0][1], str)


def test_save_roundtrip(tmp_path, sim: CitySimulation) -> None:
    path = tmp_path / "city.json"
    assert save_game(sim, str(path)) is True
    source = _sim()
    assert source.world.seed == 77
    loaded = _sim()
    assert load_game(loaded, str(path)) is True
    assert loaded.world.seed == source.world.seed
    assert loaded.day == source.day


def test_apply_save_rejects_bad_payload(sim: CitySimulation) -> None:
    assert apply_save(sim, {"t": "not-a-list"}) is False


def test_save_file_is_json(tmp_path, sim: CitySimulation) -> None:
    path = tmp_path / "city.json"
    save_game(sim, str(path))
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
