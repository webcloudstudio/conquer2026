"""
Economy engine — translates economyA.c / computeX.c / sectorX.c logic to Python.

Reference: gpl-release/Src/economyA.c, gpl-release/Src/computeX.c,
           gpl-release/Src/sectorX.c, gpl-release/Src/dataX.c
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Resource container
# ---------------------------------------------------------------------------

@dataclass
class Resources:
    talons: int = 0
    jewels: int = 0
    metals: int = 0
    food: int = 0
    wood: int = 0

    def __add__(self, other: Resources) -> Resources:
        return Resources(
            talons=self.talons + other.talons,
            jewels=self.jewels + other.jewels,
            metals=self.metals + other.metals,
            food=self.food + other.food,
            wood=self.wood + other.wood,
        )

    def __mul__(self, factor: float) -> Resources:
        return Resources(
            talons=int(self.talons * factor),
            jewels=int(self.jewels * factor),
            metals=int(self.metals * factor),
            food=int(self.food * factor),
            wood=int(self.wood * factor),
        )

    def __sub__(self, other: Resources) -> Resources:
        return Resources(
            talons=self.talons - other.talons,
            jewels=self.jewels - other.jewels,
            metals=self.metals - other.metals,
            food=self.food - other.food,
            wood=self.wood - other.wood,
        )


# ---------------------------------------------------------------------------
# Terrain lookup tables — from gpl-release/Src/dataX.c
#
# Altitude (ELE_*): WATER=0, VALLEY=1, CLEAR=2, HILL=3, MOUNTAIN=4, PEAK=5
# Each entry: (food_val, wood_val)
# ---------------------------------------------------------------------------
_ELE_INFO: list[tuple[int, int]] = [
    (0, 0),   # WATER
    (1, 0),   # VALLEY
    (1, 0),   # CLEAR / FLAT
    (0, 0),   # HILL
    (-1, -1), # MOUNTAIN
    (-2, -2), # PEAK
]

# Vegetation (VEG_*): Python model Vegetation enum → food_val, wood_val
# Mapping: NONE=0, SPARSE=1, GRASSLAND=2, FOREST=3, JUNGLE=4, SWAMP=5,
#          DESERT=6, TUNDRA=7, TAIGA=8, WETLAND=9, MEADOW=10, SCRUB=11
# Reference C veg_info table (dataX.c):
#   volcano=0,0 | desert=0,0 | tundra=0,0 | barren=4,0 | lt_veg=6,1
#   good=9,2   | wood=7,4  | forest=4,8 | jungle=0,10 | swamp=0,0
#   ice=0,0    | none=0,0
_VEG_INFO: list[tuple[int, int]] = [
    (0, 0),   # 0 NONE      → VEG_NONE
    (4, 0),   # 1 SPARSE    → VEG_BARREN
    (9, 2),   # 2 GRASSLAND → VEG_GOOD
    (4, 8),   # 3 FOREST    → VEG_FOREST
    (0, 10),  # 4 JUNGLE    → VEG_JUNGLE
    (0, 0),   # 5 SWAMP     → VEG_SWAMP
    (0, 0),   # 6 DESERT    → VEG_DESERT
    (0, 0),   # 7 TUNDRA    → VEG_TUNDRA
    (7, 4),   # 8 TAIGA     → VEG_WOOD (wooded tundra)
    (6, 1),   # 9 WETLAND   → VEG_LT_VEG
    (9, 2),   # 10 MEADOW   → VEG_GOOD
    (6, 1),   # 11 SCRUB    → VEG_LT_VEG
]

# ---------------------------------------------------------------------------
# Designation production tables — from gpl-release/Src/dataX.c  maj_dinfo[]
#
# Each entry: (production[spring,summer,fall,winter], tax_value,
#              mtrls_spt[talons,jewels,metals,food,wood])
# Designation indices match app/models/sector.py Designation enum:
#   UNDESIGNATED=0, FARM=1, MINE=2, CITY=3, FORTRESS=4, SHRINE=5,
#   FOREST=6, WASTELAND=7, ROAD=8, PORT=9, CAPITAL=10, RUINS=11,
#   PASTURE=12, ORCHARD=13, QUARRY=14, TRADE_POST=15
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class _DesigInfo:
    production: tuple[int, int, int, int]  # spring/summer/fall/winter
    tax_value: int
    mtrls_spt: tuple[int, int, int, int, int]  # talons/jewels/metals/food/wood


_DESIG_INFO: list[_DesigInfo] = [
    # 0  UNDESIGNATED — produces nothing
    _DesigInfo((0, 0, 0, 0), 0, (0, 0, 0, 0, 0)),
    # 1  FARM — high food production (no winter)
    _DesigInfo((50, 50, 50, 0), 5, (20, 0, 0, 0, 0)),
    # 2  MINE (metal mine) — steady metals, slight jewels
    _DesigInfo((95, 105, 95, 75), 9, (60, 0, 10, 0, 5)),
    # 3  CITY — moderate food + talons
    _DesigInfo((30, 30, 30, 20), 15, (50, 0, 0, 40, 0)),
    # 4  FORTRESS — small production, high support cost
    _DesigInfo((10, 10, 10, 10), 5, (80, 0, 20, 20, 0)),
    # 5  SHRINE — spiritual focus, low production
    _DesigInfo((10, 10, 10, 10), 5, (30, 0, 0, 10, 0)),
    # 6  FOREST — heavy wood output
    _DesigInfo((40, 40, 40, 20), 4, (10, 0, 0, 0, 0)),
    # 7  WASTELAND — very low output
    _DesigInfo((5, 5, 5, 5), 1, (0, 0, 0, 0, 0)),
    # 8  ROAD — supports movement, minimal production
    _DesigInfo((5, 5, 5, 5), 2, (10, 0, 0, 0, 0)),
    # 9  PORT — naval hub, good trade income
    _DesigInfo((25, 25, 25, 20), 12, (40, 0, 10, 10, 5)),
    # 10 CAPITAL — high production across all types
    _DesigInfo((40, 40, 40, 30), 20, (100, 5, 10, 60, 5)),
    # 11 RUINS — barely habitable
    _DesigInfo((5, 5, 5, 0), 1, (0, 0, 0, 0, 0)),
    # 12 PASTURE — food and wood
    _DesigInfo((35, 40, 35, 10), 4, (10, 0, 0, 10, 0)),
    # 13 ORCHARD — consistent food
    _DesigInfo((30, 60, 45, 0), 6, (15, 0, 0, 5, 0)),
    # 14 QUARRY — stone/metals
    _DesigInfo((80, 80, 80, 60), 7, (40, 0, 5, 0, 0)),
    # 15 TRADE_POST — jewels and talons
    _DesigInfo((20, 20, 20, 15), 18, (30, 5, 0, 10, 0)),
]

# ---------------------------------------------------------------------------
# Season mapping: 0=spring, 1=summer, 2=fall, 3=winter
# Turn number → season (quarter-year cycle)
# ---------------------------------------------------------------------------

def _season_index(turn: int) -> int:
    """Return season index (0–3) for a given turn number."""
    return turn % 4


def _altitude_index(altitude: int) -> int:
    """Map raw altitude int to ELE_* index (0–5)."""
    if altitude <= 0:
        return 0  # WATER
    if altitude <= 2:
        return 1  # VALLEY
    if altitude <= 5:
        return 2  # CLEAR
    if altitude <= 7:
        return 3  # HILL
    if altitude <= 9:
        return 4  # MOUNTAIN
    return 5      # PEAK


def _poptoworkers(population: int) -> int:
    """Convert population to effective worker count.

    Reference: economyA.c :: poptoworkers()
    Approximately 10% of population are active workers.
    """
    return max(0, population // 10)


def _tofood(altitude_idx: int, vegetation_idx: int) -> int:
    """Compute food value modifier for terrain. Reference: sectorX.c :: tofood()"""
    veg_food = _VEG_INFO[vegetation_idx][0] if vegetation_idx < len(_VEG_INFO) else 0
    ele_food = _ELE_INFO[altitude_idx][0] if altitude_idx < len(_ELE_INFO) else 0
    return max(0, veg_food + ele_food)


def _towood(altitude_idx: int, vegetation_idx: int) -> int:
    """Compute wood value modifier for terrain. Reference: sectorX.c :: towood()"""
    veg_wood = _VEG_INFO[vegetation_idx][1] if vegetation_idx < len(_VEG_INFO) else 0
    ele_wood = _ELE_INFO[altitude_idx][1] if altitude_idx < len(_ELE_INFO) else 0
    return max(0, veg_wood + ele_wood)


def _jewel_value(minerals: int, altitude_idx: int) -> int:
    """Compute jewel production potential. Reference: sectorX.c :: jewel_value()"""
    # Gems found in mountains; minerals field amplifies further
    ele_bonus = max(0, altitude_idx - 2)  # hill+ has gems
    return max(0, minerals // 3 + ele_bonus)


def _metal_value(minerals: int, altitude_idx: int) -> int:
    """Compute metal production potential. Reference: sectorX.c :: metal_value()"""
    # Metals found in hills and mountains
    ele_bonus = max(0, altitude_idx - 2) * 2
    return max(0, minerals + ele_bonus)


# ---------------------------------------------------------------------------
# Core production function
# ---------------------------------------------------------------------------

def compute_sector_production(
    designation: int,
    efficiency: int,
    population: int,
    altitude: int,
    vegetation: int,
    tradegood: int,
    minerals: int = 0,
    turn: int = 0,
) -> Resources:
    """
    Compute one turn's resource output for a single sector.

    Reference: sectorX.c :: sector_produce(), dataX.c maj_dinfo table.

    Formula (matches C original):
      workpop = poptoworkers(population)
      pval = maj_dinfo[designation].production[season] * efficiency / 100
      food = tofood(terrain) * workpop * pval / 100
      wood = 10 * towood(terrain) * workpop * pval / 100  (but scaled to 1/10)
      metals = metal_value * workpop * pval / 100
      jewels = jewel_value * workpop * pval / 100
      talons = prod_amount * tax_value   (where prod_amount = workpop * pval / 100)
    """
    if designation < 0 or designation >= len(_DESIG_INFO):
        designation = 0

    desig = _DESIG_INFO[designation]
    season = _season_index(turn)
    base_pval = desig.production[season]

    if base_pval == 0 or population <= 0:
        return Resources()

    # Efficiency scales production (0–100, can slightly exceed 100 with bonuses)
    pval = base_pval * max(0, efficiency) // 100

    workpop = _poptoworkers(population)
    alt_idx = _altitude_index(altitude)
    veg_idx = vegetation if 0 <= vegetation < len(_VEG_INFO) else 0

    # Core production values
    tf = _tofood(alt_idx, veg_idx)
    tw = _towood(alt_idx, veg_idx)
    mv = _metal_value(minerals, alt_idx)
    jv = _jewel_value(minerals, alt_idx)

    # prod_amount = workers × production_rate (matches C pattern)
    prod_amount = workpop * pval // 100

    # Resource outputs (clamped to >= 0)
    food = max(0, tf * workpop * pval // 100)
    wood = max(0, tw * workpop * pval // 1000)   # /1000 to scale
    metals = max(0, mv * workpop * pval // 10000)
    jewels = max(0, jv * workpop * pval // 10000)
    talons = max(0, prod_amount * desig.tax_value)

    # Subsistence bonus: sectors with people always produce a little food & wood
    # (mirrors C: "if people > 100" base production lines)
    if population > 100:
        food += 1
        if tw > 0:
            wood += 1

    # Trade good bonus: tradegood sector gives extra talons
    if tradegood > 0:
        talons += tradegood * prod_amount // 100

    return Resources(
        talons=talons,
        jewels=jewels,
        metals=metals,
        food=food,
        wood=wood,
    )


# ---------------------------------------------------------------------------
# Sector consumption
# ---------------------------------------------------------------------------

def compute_sector_consumption(
    designation: int,
    population: int,
    eatrate: int = 1,
) -> Resources:
    """
    Compute resources consumed by a sector per turn.

    Reference: sectorX.c :: sector_consume(), economyA.c :: upd_consume()

    Civilians eat food at eatrate per person.
    The designation's mtrls_spt[] array specifies support costs per 1000 pop.
    """
    if population <= 0:
        return Resources()

    desig = _DESIG_INFO[max(0, min(designation, len(_DESIG_INFO) - 1))]

    # Food consumption: eatrate is expressed per 1000 people (BUTE_EATRATE scale)
    # Default eatrate ~1 means ~1 food per 1000 people per turn
    food_consumed = max(0, population * max(1, eatrate) // 1000)

    # Designation support costs (per 1000 population, scaled)
    scale = max(1, population // 1000)
    spt = desig.mtrls_spt
    return Resources(
        talons=spt[0] * scale,
        jewels=spt[1] * scale,
        metals=spt[2] * scale,
        food=food_consumed + spt[3] * scale,
        wood=spt[4] * scale,
    )


# ---------------------------------------------------------------------------
# Army upkeep
# ---------------------------------------------------------------------------

# Army upkeep constants from header.h.dist
_NAVYMAINT = 4000     # cost per navy turn
_CVNMAINT = 1000      # cost per caravan turn
_WAGONS_IN_CVN = 10   # wagons per caravan unit

# Unit type constants matching armyX.h / ainfo_list categories
_ARMY_TYPE_MONSTER = 2   # AC_MONSTER
_ARMY_TYPE_LEADER = 0    # AC_LEADER
_ARMY_TYPE_SPELLCASTER = 1  # AC_SPELLCASTER


def compute_army_upkeep(unit_type: int, strength: int, supply: int) -> Resources:
    """
    Compute food/talon cost to maintain an army unit for one turn.

    Reference: economyA.c :: army_support() / upd_sectors()

    Normal armies consume food proportional to strength.
    Monsters consume jewels (and food).
    Leaders/spellcasters are small fixed-cost units.
    supply=0 means the unit is far from its supply chain (higher cost).
    """
    if strength <= 0:
        return Resources()

    # Supply penalty: out-of-supply units cost double
    supply_factor = 1.0 if supply > 0 else 2.0

    if unit_type == _ARMY_TYPE_MONSTER:
        # Monsters eat jewels (from economyA.c monster maintenance)
        jewels = int(math.ceil(strength / 50.0 * supply_factor))
        food = int(math.ceil(strength / 100.0 * supply_factor))
        return Resources(jewels=jewels, food=food)

    if unit_type in (_ARMY_TYPE_LEADER, _ARMY_TYPE_SPELLCASTER):
        # Leaders are individuals; small flat cost
        food = int(math.ceil(1 * supply_factor))
        return Resources(food=food)

    # Normal army: 1 food per 100 men
    food = int(math.ceil(strength / 100.0 * supply_factor))
    return Resources(food=food)


def compute_navy_upkeep(crew: int, supply: int) -> Resources:
    """Navy maintenance: fixed cost per crew unit. Reference: economyA.c"""
    if crew <= 0:
        return Resources()
    supply_factor = 1.0 if supply > 0 else 2.0
    return Resources(
        talons=int(_NAVYMAINT * supply_factor // 1000),
        food=int(math.ceil(crew / 50.0 * supply_factor)),
    )


def compute_caravan_upkeep(size: int) -> Resources:
    """Caravan maintenance. Reference: economyA.c (CVNMAINT constant)"""
    if size <= 0:
        return Resources()
    return Resources(talons=size * _CVNMAINT // _WAGONS_IN_CVN)


# ---------------------------------------------------------------------------
# Caravan delivery value
# ---------------------------------------------------------------------------

def compute_caravan_value(
    cargo: Resources,
    source_x: int,
    source_y: int,
    dest_x: int,
    dest_y: int,
    efficiency: int,
    trader_class_bonus: float = 1.0,
) -> int:
    """
    Compute the talon value of a caravan delivery.

    Value scales with distance and cargo rarity.
    Trader class gets a bonus multiplier (default 1.0, Trader class = 2.0).

    Reference: caravanG.c :: caravan_deliver()
    Hex distance measured with offset-coordinate formula from hexmapX.c.
    """
    # Hex distance (simplified for offset grid)
    dx = abs(dest_x - source_x)
    dy = abs(dest_y - source_y)
    dist = max(dx, dy, (dx + dy) // 2)

    if dist == 0:
        return 0

    # Base talon value: sum all cargo materials weighted by rarity
    # Jewels most valuable, then metals, then food/wood, talons face value
    raw_value = (
        cargo.talons
        + cargo.jewels * 5
        + cargo.metals * 3
        + cargo.food * 1
        + cargo.wood * 2
    )

    # Distance bonus (diminishing returns beyond 10 hexes)
    dist_multiplier = 1.0 + min(dist, 20) * 0.05

    # Efficiency scales the delivery
    eff_factor = max(0.0, efficiency / 100.0)

    result = int(raw_value * dist_multiplier * eff_factor * trader_class_bonus)
    return max(0, result)


# ---------------------------------------------------------------------------
# Tax income
# ---------------------------------------------------------------------------

def apply_tax_rate(population: int, tax_rate: int, morale: int) -> int:
    """
    Compute talon income from a civilian population.

    Reference: economyA.c :: tax_income() / adjust_production()

    Formula: base = population * taxrate / 100
    Morale modifier: income reduced when morale is very low (< 50).
    High tax (> 50) reduces morale and may trigger unrest.
    """
    if population <= 0:
        return 0

    base_income = population * max(0, tax_rate) // 100

    # Morale modifier: below 50 morale, income drops linearly to 50%
    morale_clamped = max(0, min(100, morale))
    if morale_clamped < 50:
        morale_factor = 0.5 + morale_clamped / 100.0
    else:
        morale_factor = 1.0

    return int(base_income * morale_factor)


# ---------------------------------------------------------------------------
# Production adjustments (magic / attribute bonuses)
# ---------------------------------------------------------------------------

# Magic civilian sub-power constants (from magicX.h / computeX.c)
_MC_FARMING = 0x01   # +20% food production
_MC_MINER = 0x02     # +20% jewels and metals
_MW_EARTH = 0x04     # +10% metals (wizardry)
_MW_DRUIDISM = 0x08  # +20% wood (wizardry)


def adjust_production(
    produced: Resources,
    taxrate: int,
    civ_magic: int = 0,
    wiz_magic: int = 0,
) -> Resources:
    """
    Apply attribute and magic bonuses to a nation's total production.

    Reference: computeX.c :: adjust_production()

    taxrate (BUTE_TAXRATE): scales talon income.
    civ_magic / wiz_magic: bitmask of active civilian/wizardry sub-powers.
    """
    talons = produced.talons * max(0, taxrate) // 100
    food = produced.food
    wood = produced.wood
    jewels = produced.jewels
    metals = produced.metals

    # Civilian magic bonuses
    if civ_magic & _MC_FARMING:
        food = food * 120 // 100
    if civ_magic & _MC_MINER:
        jewels = jewels * 120 // 100
        metals = metals * 120 // 100

    # Wizardry magic bonuses
    if wiz_magic & _MW_EARTH:
        metals = metals * 110 // 100
    if wiz_magic & _MW_DRUIDISM:
        wood = wood * 120 // 100

    return Resources(
        talons=talons,
        jewels=jewels,
        metals=metals,
        food=food,
        wood=wood,
    )
