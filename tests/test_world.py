"""Tests for the world / tile grid."""

from cityforge import content as C
from cityforge.world import World


def test_world_tile_count(world: World) -> None:
    assert len(world.tiles) == world.size * world.size


def test_world_tile_coordinates(world: World) -> None:
    assert world.tile_at(0, 0).x == 0
    assert world.tile_at(0, 0).y == 0
    assert world.tile_at(3, 5).x == 3
    assert world.tile_at(3, 5).y == 5
    assert world.tile_at(-1, 0) is None
    assert world.tile_at(0, -1) is None


def test_world_index_roundtrip(world: World) -> None:
    assert world.index(3, 5) == 5 * world.size + 3


def test_world_cover_power_and_water(world: World) -> None:
    world.tiles[0].kind = "power"
    grids = world.cover()
    assert "power" in grids
    assert "water" in grids
    assert len(grids["power"]) == world.size * world.size
    assert len(grids["water"]) == world.size * world.size


def test_world_near_road(world: World) -> None:
    world.tiles[0].kind = "road"
    assert world.near_road(1, 0, radius=2)
    assert not world.near_road(10, 10, radius=1)


def test_world_near_industrial(world: World) -> None:
    world.tiles[0].kind = "ind"
    world.tiles[0].level = 2
    assert world.near_industrial(0, 0)
    world.tiles[0].level = 0
    assert not world.near_industrial(0, 0)
