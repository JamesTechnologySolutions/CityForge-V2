"""Shared test fixtures."""

from __future__ import annotations

import pytest

from cityforge.config import GameConfig
from cityforge.model import HudSnapshot
from cityforge.simulation import CitySimulation
from cityforge.traffic import TrafficSystem
from cityforge.world import World


@pytest.fixture
def config() -> GameConfig:
    return GameConfig()


@pytest.fixture
def world() -> World:
    return World(seed=20240617, size=56, tile_width=64, tile_height=32)


@pytest.fixture
def sim(config: GameConfig, world: World) -> CitySimulation:
    return CitySimulation(config=config, world=world, traffic=TrafficSystem(world), disasters=None)


@pytest.fixture
def snapshot() -> HudSnapshot:
    return HudSnapshot()
