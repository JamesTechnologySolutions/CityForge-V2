"""City simulation: economy, demand, growth, happiness, ranks and budget."""

from __future__ import annotations

import random
from typing import Callable, Optional

from cityforge import content as C
from cityforge.config import GameConfig
from cityforge.model import HudSnapshot
from cityforge.rng import Lcg
from cityforge.world import World

ZONE_KINDS: tuple[str, ...] = ("res", "com", "ind")


def _clamp(value: float, lower: float = -1.0, upper: float = 1.0) -> float:
    """Clamp ``value`` into ``[lower, upper]``."""
    return max(lower, min(upper, value))


class CitySimulation:
    """Mutable simulation state of a single city.

    This class owns *only* simulation state.  Rendering, audio and UI are
    separate collaborators that read from it.
    """

    def __init__(
        self,
        config: GameConfig,
        seed: Optional[int] = None,
        world: Optional[World] = None,
        traffic: Optional["object"] = None,
        disasters: Optional["object"] = None,
        on_rank_up: Optional[Callable[[int], None]] = None,
        on_autosave: Optional[Callable[[], None]] = None,
        on_funds_warning: Optional[Callable[[], None]] = None,
    ) -> None:
        self.config = config
        self.rng = Lcg(seed if seed is not None else int(random.Random().random() * 1e9))
        self.world = world if world is not None else World(
            seed=int(seed) if seed is not None else self.rng.state,
            size=config.map_size,
            tile_width=config.tile_width,
            tile_height=config.tile_height,
        )
        self.traffic = traffic
        self.disasters = disasters
        self.on_rank_up = on_rank_up if on_rank_up is not None else (lambda _rank: None)
        self.on_autosave = on_autosave if on_autosave is not None else (lambda: None)
        self.on_funds_warning = on_funds_warning if on_funds_warning is not None else (lambda: None)

        self.money: float = float(config.initial_money)
        self.day: int = 0
        self.tax: float = float(config.start_tax_rate)
        self.speed: int = 1
        self.name: str = "Newtown"
        self.pop: float = 0.0
        self.jobs: float = 0.0
        self.happy: float = float(config.start_happiness)
        self.dem: dict[str, float] = {"r": 1.0, "c": 1.0, "i": 1.0}
        self.inc: float = 0.0
        self.exp: float = 0.0
        self.rank: int = 0
        self.cong: float = 0.0
        self.coverage: dict[str, list[bool]] = {}
        self.snapshot: HudSnapshot = HudSnapshot()

    # ------------------------------------------------------------------ helpers
    def _covered(self, category: str, index: int) -> bool:
        grid = self.coverage.get(category)
        if grid is None:
            return False
        return bool(grid[index])

    def near_industrial(self, x: int, y: int) -> bool:
        return self.world.near_industrial(x, y, radius=4)

    # ------------------------------------------------------------------ tick
    def tick(self) -> None:
        """Advance the simulation by one in-game day."""
        self.day += 1
        self.coverage = self.world.cover()
        expense = 0.0
        pop = 0.0
        jobs_com = 0.0
        jobs_ind = 0.0
        happy_sum = 0.0
        happy_units = 0.0

        for tile in self.world.tiles:
            definition = C.TOOLS.get(tile.kind) if tile.kind is not None else None
            if definition is not None and definition.daily_upkeep:
                expense += definition.daily_upkeep
            if tile.kind == "road":
                expense += C.ROAD_DAILY_UPKEEP
            if tile.kind not in ZONE_KINDS:
                continue
            tile.road = self.world.near_road(tile.x, tile.y, radius=2)
            tile.powered = self._covered("power", self.world.index(tile.x, tile.y))
            tile.water_supply = self._covered("water", self.world.index(tile.x, tile.y))
            if tile.level > 0 and tile.road and tile.powered:
                if tile.kind == "res":
                    pop += tile.level * C.TOOLS["res"].homes_per_level
                    happiness = C.HAPPINESS_BASELINE
                    for category, bonus in C.HAPPINESS_BONUSES.items():
                        if self._covered(category, self.world.index(tile.x, tile.y)):
                            happiness += bonus
                    if self.near_industrial(tile.x, tile.y):
                        happiness -= C.NEIGHBOR_UNHAPPY_PENALTY
                    happiness -= max(0.0, self.tax - C.TAX_BASELINE) * C.TAX_UNHAPPY_FACTOR
                    happiness -= self.cong * C.CONGESTION_UNHAPPY_FACTOR
                    tile.happiness = happiness
                    happy_sum += happiness * tile.level
                    happy_units += tile.level
                elif tile.kind == "com":
                    jobs_com += tile.level * C.TOOLS["com"].jobs_per_level
                elif tile.kind == "ind":
                    jobs_ind += tile.level * C.TOOLS["ind"].jobs_per_level

        jobs = jobs_com + jobs_ind
        self.pop = pop
        self.jobs = jobs
        self.happy = max(0.0, min(100.0, happy_sum / happy_units)) if happy_units else 50.0

        jd = (pop * C.DEMAND_RESIDENTIAL - jobs + C.DEMAND_STABILITY) / (pop * C.DEMAND_RESIDENTIAL + jobs + C.DEMAND_STABILITY)
        rd = (jobs * C.DEMAND_JOB_FACTOR + C.DEMAND_STABILITY - pop) / (jobs * C.DEMAND_JOB_FACTOR + pop + C.DEMAND_STABILITY)
        tax_term = (self.tax - C.TAX_BASELINE) * C.TAX_RATE_DEMAND_FACTOR
        happiness_term = (self.happy - 50.0) / 100.0 * C.HAPPINESS_DEMAND_FACTOR
        margin_com = C.DEMAND_GROWTH_MARGIN if jobs_ind > jobs_com * 1.5 else C.DEMAND_DECLINE_MARGIN
        margin_ind = C.DEMAND_INDUSTRIAL_MARGIN if jobs_com > jobs_ind * 0.8 else C.DEMAND_DECLINE_MARGIN
        self.dem = {
            "r": _clamp(rd - tax_term + happiness_term),
            "c": _clamp(jd - tax_term + margin_com),
            "i": _clamp(jd - tax_term + margin_ind),
        }

        for tile in self.world.tiles:
            if tile.kind not in ZONE_KINDS:
                continue
            demand = self.dem[tile.kind[0]]
            if (
                tile.level > 0
                and tile.road
                and tile.powered
                and not tile.fire
                and tile.level < C.TOOLS[tile.kind].max_level
                and (tile.level < 2 or tile.water_supply)
                and self.rng.next_float() < C.TOOLS[tile.kind].growth_chance * max(0.0, demand) * (1.0 - self.cong * 0.5)
            ):
                tile.level += 1
            elif tile.level > 0 and (
                (not tile.road or not tile.powered) and self.rng.next_float() < 0.05
            ) or (demand < -0.3 and self.rng.next_float() < 0.03):
                tile.level -= 1

        if self.traffic is not None:
            self.cong = self.traffic.update(self)

        income = (self.tax / C.INCOME_PER_TAX_UNIT) * (
            pop * C.INCOME_PER_CAPITA + jobs_com * C.INCOME_PER_JOB_COMMERCIAL + jobs_ind * C.INCOME_PER_JOB_INDUSTRIAL
        )
        self.inc = income
        self.exp = expense
        self.money += income - expense

        if self.disasters is not None:
            self.disasters.run(self)

        self._update_rank()
        self._update_funds_warning()
        self._update_autosave()
        self.refresh_snapshot()

    def _update_rank(self) -> None:
        rank_index = 0
        for index, (threshold, _name) in enumerate(C.RANKS):
            if self.pop >= threshold:
                rank_index = index
        if rank_index > self.rank:
            self.rank = rank_index
            self.on_rank_up(rank_index)
        elif rank_index < self.rank:
            self.rank = rank_index

    def _update_funds_warning(self) -> None:
        if self.money < 0 and self.day % self.config.autosave_day_interval == 0:
            self.on_funds_warning()

    def _update_autosave(self) -> None:
        if self.day % self.config.autosave_day_interval == 0:
            self.on_autosave()

    # ------------------------------------------------------------------ snapshot
    def refresh_snapshot(self) -> HudSnapshot:
        net = self.inc - self.exp
        snapshot = HudSnapshot(
            money=self.money,
            day=self.day,
            tax=self.tax,
            speed=self.speed,
            name=self.name,
            pop=self.pop,
            jobs=self.jobs,
            happy=self.happy,
            dem_residential=self.dem.get("r", 1.0),
            dem_commercial=self.dem.get("c", 1.0),
            dem_industrial=self.dem.get("i", 1.0),
            income=self.inc,
            expense=self.exp,
            net=net,
            rank=self.rank,
        )
        self.snapshot = snapshot
        return snapshot
