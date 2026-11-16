"""Data-driven game content: tools, services, zones, ranks and layers."""

from __future__ import annotations

from dataclasses import dataclass

# Daily upkeep charged to the city budget for every road tile.
ROAD_DAILY_UPKEEP: float = 0.15

# Happiness bonus granted by service coverage (see :data:`HAPPINESS_BONUSES`).
HAPPINESS_BONUSES: dict[str, float] = {
    "school": 10.0,
    "clinic": 12.0,
    "police": 10.0,
    "park": 8.0,
    "fire": 6.0,
    "water": 12.0,
}

HAPPINESS_BASELINE: float = 38.0
NEIGHBOR_UNHAPPY_PENALTY: float = 15.0
TAX_UNHAPPY_FACTOR: float = 3.0
CONGESTION_UNHAPPY_FACTOR: float = 15.0
TAX_BASELINE: float = 9.0
TAX_RATE_DEMAND_FACTOR: float = 0.04
HAPPINESS_DEMAND_FACTOR: float = 0.3

CAR_COLORS: tuple[str, ...] = (
    "#e8e8e8",
    "#d9453d",
    "#3d7bd9",
    "#e0b43f",
    "#2b2f36",
    "#4cae6a",
)

DEMAND_RESIDENTIAL: float = 0.8
DEMAND_JOB_FACTOR: float = 1.1
DEMAND_STABILITY: float = 25.0
DEMAND_GROWTH_MARGIN: float = 0.25
DEMAND_DECLINE_MARGIN: float = -0.1
DEMAND_INDUSTRIAL_MARGIN: float = 0.15

INCOME_PER_CAPITA: float = 0.35
INCOME_PER_JOB_COMMERCIAL: float = 0.6
INCOME_PER_JOB_INDUSTRIAL: float = 0.45
INCOME_PER_TAX_UNIT: float = 9.0

VELOCITY_PER_SPEED_STEP: float = 1.3
VELOCITY_CAP_NOMINAL: float = 1.0
VELOCITY_CONGESTION_DECAY: float = 0.65
VELOCITY_CONGESTION_THRESHOLD: float = 14.0
CAR_SPAWN_PER_RESIDENT: float = 10.0
CAR_SPAWN_PER_JOB: float = 16.0
CAR_TARGET_PER_RESIDENT: float = 10.0
CAR_TARGET_PER_JOB: float = 16.0
CAR_TARGET_MIN: int = 0
CAR_TARGET_MAX: int = 160
CAR_SPEED_PER_SPEED_STEP: tuple[float, ...] = (0.0, 1.0, 2.2, 4.0)

FIRE_TICKS: int = 6
FIRE_SPREAD_BASE: float = 0.07
FIRE_SPREAD_INFERNO: float = 0.2
FIRE_INFERNO_COVERAGE_FACTOR: float = 0.15
FIRE_EXTINGUISH_CHANCE: float = 0.5
FIRE_TILE_RADIUS: int = 2

DISASTER_FIRE_CHANCE: float = 0.012
DISASTER_QUAKE_CHANCE: float = 0.0015
DISASTER_TORNADO_CHANCE: float = 0.003
EARTHQUAKE_ZONE_DAMAGE_CHANCE: float = 0.12
EARTHQUAKE_BUILDING_DAMAGE_CHANCE: float = 0.03
TORNADO_HITS: int = 16

BULL_COST: int = 2


@dataclass(frozen=True)
class ToolDef:
    """Definition of a placeable object (zone, service or tool)."""

    kind: str
    name: str
    color: str
    cost: int
    group: str
    info: str
    coverage_radius: int = 0
    coverage_category: str | None = None
    daily_upkeep: float = 0.0
    height: int = 0
    max_level: int = 3
    jobs_per_level: float = 0.0
    homes_per_level: float = 0.0
    traffic_load_per_level: float = 3.0
    provides_power: bool = False
    grows_with_road_and_power: bool = True
    requires_water_for_level3: bool = True
    growth_chance: float = 0.12

    @property
    def is_zone(self) -> bool:
        return self.kind in ("res", "com", "ind")

    @property
    def is_service(self) -> bool:
        return self.coverage_radius > 0 and self.daily_upkeep > 0


TOOLS: dict[str, ToolDef] = {
    "road": ToolDef(
        kind="road", name="Road", color="#46515c", cost=10, group="Build", info="Connects zones. Costs 0.15/day.",
    ),
    "res": ToolDef(
        kind="res", name="Residential", color="#58b86f", cost=20, group="Zones", info="Homes. Need road + power.",
        homes_per_level=10.0, traffic_load_per_level=3.0,
    ),
    "com": ToolDef(
        kind="com", name="Commercial", color="#4f93e0", cost=20, group="Zones", info="Shops and offices. Provide jobs.",
        jobs_per_level=6.0, traffic_load_per_level=4.0,
    ),
    "ind": ToolDef(
        kind="ind", name="Industrial", color="#e0a93f", cost=20, group="Zones", info="Factories. Jobs, but unhappy neighbors.",
        jobs_per_level=8.0, traffic_load_per_level=3.0,
    ),
    "power": ToolDef(
        kind="power", name="Power plant", color="#e2573f", cost=900, group="Services", info="Powers zones within 16 tiles.",
        coverage_radius=16, daily_upkeep=18.0, height=34, max_level=1, provides_power=True,
    ),
    "solar": ToolDef(
        kind="solar", name="Solar farm", color="#27406b", cost=600, group="Services", info="Clean power within 9 tiles.",
        coverage_radius=9, daily_upkeep=4.0, height=3, max_level=1, provides_power=True, coverage_category="power",
    ),
    "water": ToolDef(
        kind="water", name="Water tower", color="#4fb7e0", cost=500, group="Services", info="Water within 12 tiles. Needed for level 3.",
        coverage_radius=12, daily_upkeep=6.0, height=30, max_level=1,
    ),
    "park": ToolDef(
        kind="park", name="Park", color="#2f9e57", cost=80, group="Services", info="Raises happiness within 5 tiles.",
        coverage_radius=5, daily_upkeep=1.0, height=0, max_level=1,
    ),
    "school": ToolDef(
        kind="school", name="School", color="#a770dc", cost=400, group="Services", info="Raises happiness within 9 tiles.",
        coverage_radius=9, daily_upkeep=7.0, height=24, max_level=1,
    ),
    "clinic": ToolDef(
        kind="clinic", name="Clinic", color="#eef1f6", cost=450, group="Services", info="Raises happiness within 9 tiles.",
        coverage_radius=9, daily_upkeep=8.0, height=24, max_level=1,
    ),
    "police": ToolDef(
        kind="police", name="Police", color="#4a66e0", cost=400, group="Services", info="Raises happiness within 10 tiles.",
        coverage_radius=10, daily_upkeep=7.0, height=22, max_level=1,
    ),
    "fire": ToolDef(
        kind="fire", name="Fire station", color="#e8562f", cost=450, group="Services", info="Fights fires within 10 tiles.",
        coverage_radius=10, daily_upkeep=8.0, height=22, max_level=1,
    ),
    "hospital": ToolDef(
        kind="hospital", name="Hospital", color="#f2f5fa", cost=1400, group="Services", info="Large medical coverage, 16 tiles.",
        coverage_radius=16, coverage_category="clinic", daily_upkeep=20.0, height=36, max_level=1,
    ),
    "bull": ToolDef(
        kind="bull", name="Bulldoze", color="#b4503f", cost=BULL_COST, group="Tools", info="Clears a tile.",
    ),
}

GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Build", ("road",)),
    ("Zones", ("res", "com", "ind")),
    ("Services", ("power", "solar", "water", "park", "school", "clinic", "hospital", "police", "fire")),
    ("Tools", ("bull",)),
)

TOOLS_ORDER: tuple[str, ...] = (
    "road", "res", "com", "ind", "bull", "power", "solar", "water", "park", "school", "clinic", "police", "fire", "hospital",
)

DRAG_TOOLS: frozenset[str] = frozenset({"road", "res", "com", "ind", "bull"})

RANKS: tuple[tuple[int, str], ...] = (
    (0, "Hamlet"),
    (100, "Village"),
    (500, "Town"),
    (1500, "City"),
    (5000, "Large city"),
    (15000, "Metropolis"),
)

MONTHS: tuple[str, ...] = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)

LAYER_ORDER: tuple[tuple[str | None, str], ...] = (
    (None, "Off"),
    ("power", "Power"),
    ("water", "Water"),
    ("police", "Police"),
    ("fire", "Fire"),
    ("clinic", "Health"),
    ("traffic", "Traffic"),
    ("happy", "Happiness"),
)

COVERAGE_CATEGORIES: tuple[str, ...] = (
    "power",
    "water",
    "park",
    "school",
    "clinic",
    "police",
    "fire",
)
