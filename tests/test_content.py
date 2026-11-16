"""Tests for game content definitions."""

from cityforge import content as C


def test_tool_registry_contains_all_kinds() -> None:
    expected = {"road", "res", "com", "ind", "bull", "power", "solar", "water", "park", "school", "clinic", "police", "fire", "hospital"}
    assert expected.issubset(set(C.TOOLS))


def test_road_upkeep() -> None:
    assert C.TOOLS["road"].daily_upkeep == 0.0
    assert C.ROAD_DAILY_UPKEEP == 0.15


def test_solar_covers_power() -> None:
    solar = C.TOOLS["solar"]
    assert solar.coverage_category == "power"
    assert solar.coverage_radius == 9


def test_happiness_bonuses_cover_services() -> None:
    assert set(C.HAPPINESS_BONUSES) >= {"school", "clinic", "police", "park", "fire", "water"}


def test_ranks_monotonic() -> None:
    assert [rank for _threshold, rank in C.RANKS] == ["Hamlet", "Village", "Town", "City", "Large city", "Metropolis"]


def test_layer_order() -> None:
    assert C.LAYER_ORDER[0][0] is None
    assert ("traffic", "Traffic") in C.LAYER_ORDER
    assert ("happy", "Happiness") in C.LAYER_ORDER
