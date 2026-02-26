"""
Turn processor — orchestrates one full game turn.

Mirrors the execution order of gpl-release/Src/executeX.c :: execute_turn().

Turn phase order (matches C original):
  1. upd_sectors  — produce resources, consume civilian needs
  2. upd_produce  — aggregate national totals
  3. upd_consume  — deduct army/navy/caravan upkeep; handle starvation/desertion
  4. upd_armies   — movement, combat, capture resolution  (stub — Phase 3)
  5. upd_navies   — naval movement and combat             (stub — Phase 3)
  6. upd_caravans — caravan delivery                      (stub — Phase 3)
  7. upd_magic    — magic power regen, passive effects
  8. upd_events   — fire / advance world events           (stub — Phase 3)
  9. upd_victory  — compute victory points

Reference constants from header.h.dist:
  PSTARVE=25   — % of army that dies per turn without food
  PDISBAND=10  — % chance an army disbands when starving
  PVOLUNTEERS=20 — % of city population that volunteers each turn
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.engine.economy import (
    Resources,
    adjust_production,
    apply_tax_rate,
    compute_army_upkeep,
    compute_caravan_upkeep,
    compute_navy_upkeep,
    compute_sector_consumption,
    compute_sector_production,
)
from app.engine.magic import apply_passive_powers, regen_magic_power

# ---------------------------------------------------------------------------
# Starvation / desertion constants  (header.h.dist)
# ---------------------------------------------------------------------------
PSTARVE: int = 25     # % army deaths per turn without food
PDISBAND: int = 10    # % chance of disbanding when starving
PVOLUNTEERS: int = 20 # % city pop that volunteers for armies per turn
PBARNICLES: int = 2   # % base morale change per turn


# ---------------------------------------------------------------------------
# Simple in-memory representation of world state for the processor
# These mirror the ORM models but are pure Python for testability.
# ---------------------------------------------------------------------------

@dataclass
class SectorState:
    x: int
    y: int
    designation: int = 0
    altitude: int = 0
    vegetation: int = 0
    efficiency: int = 50
    population: int = 0
    minerals: int = 0
    tradegood: int = 0
    owner_nation_id: object = None


@dataclass
class ArmyState:
    id: object
    nation_id: object
    unit_type: int = 0
    strength: int = 0
    supply: int = 1
    morale: int = 70    # 0–100
    is_active: bool = True


@dataclass
class NavyState:
    id: object
    nation_id: object
    crew: int = 0
    supply: int = 1
    is_active: bool = True


@dataclass
class CaravanState:
    id: object
    nation_id: object
    size: int = 0
    is_active: bool = True


@dataclass
class NationState:
    id: object
    # 19 attributes (BUTE_* from butesX.h)
    attr_taxrate: int = 30
    attr_eatrate: int = 1
    attr_morale: int = 70
    attr_wiz_skill: int = 10
    attr_spell_pts: int = 50
    # Resources
    res_talons: int = 0
    res_jewels: int = 0
    res_metals: int = 0
    res_food: int = 0
    res_wood: int = 0
    # Magic powers
    power_military: int = 0
    power_civilian: int = 0
    power_wizardry: int = 0
    # Race / class
    race_traits: int = 0
    player_class: str = ""
    shrines_owned: int = 0
    # Victory points (new system)
    victory_points: int = 0

    def resources(self) -> Resources:
        return Resources(
            talons=self.res_talons,
            jewels=self.res_jewels,
            metals=self.res_metals,
            food=self.res_food,
            wood=self.res_wood,
        )

    def apply_resources(self, r: Resources) -> None:
        self.res_talons += r.talons
        self.res_jewels += r.jewels
        self.res_metals += r.metals
        self.res_food += r.food
        self.res_wood += r.wood

    def deduct_resources(self, r: Resources) -> None:
        self.res_talons = max(0, self.res_talons - r.talons)
        self.res_jewels = max(0, self.res_jewels - r.jewels)
        self.res_metals = max(0, self.res_metals - r.metals)
        self.res_food = max(0, self.res_food - r.food)
        self.res_wood = max(0, self.res_wood - r.wood)


@dataclass
class TurnLog:
    turn: int
    messages: list[str] = field(default_factory=list)
    sector_production: dict = field(default_factory=dict)   # nation_id → Resources
    army_starvation: dict = field(default_factory=dict)     # army_id → deaths
    magic_regen: dict = field(default_factory=dict)         # nation_id → (mil,civ,wiz)


# ---------------------------------------------------------------------------
# Phase 1 — Sector production
# ---------------------------------------------------------------------------

def upd_sectors(
    nations: dict[object, NationState],
    sectors: list[SectorState],
    turn: int,
    log: TurnLog,
) -> None:
    """
    Compute production and consumption for every owned sector.

    Reference: economyA.c :: upd_sectors()
    """
    for sct in sectors:
        if sct.owner_nation_id is None:
            continue

        ntn = nations.get(sct.owner_nation_id)
        if ntn is None:
            continue

        produced = compute_sector_production(
            designation=sct.designation,
            efficiency=sct.efficiency,
            population=sct.population,
            altitude=sct.altitude,
            vegetation=sct.vegetation,
            tradegood=sct.tradegood,
            minerals=sct.minerals,
            turn=turn,
        )

        consumed = compute_sector_consumption(
            designation=sct.designation,
            population=sct.population,
            eatrate=ntn.attr_eatrate,
        )

        # Tax income from civilian population
        tax_income = apply_tax_rate(
            population=sct.population,
            tax_rate=ntn.attr_taxrate,
            morale=ntn.attr_morale,
        )

        # Net production (production minus civilian consumption)
        net = produced + Resources(talons=tax_income)
        net = net - consumed

        # Apply magic/attribute bonuses to production
        net = adjust_production(
            net,
            taxrate=100,   # already applied tax rate above
            civ_magic=ntn.power_civilian,
            wiz_magic=ntn.power_wizardry,
        )

        ntn.apply_resources(net)

        # Accumulate per-nation production for logging
        existing = log.sector_production.get(ntn.id, Resources())
        log.sector_production[ntn.id] = existing + net


# ---------------------------------------------------------------------------
# Phase 2 — Army / navy / caravan upkeep
# ---------------------------------------------------------------------------

def upd_consume(
    nations: dict[object, NationState],
    armies: list[ArmyState],
    navies: list[NavyState],
    caravans: list[CaravanState],
    log: TurnLog,
) -> None:
    """
    Deduct upkeep for military units; apply starvation / desertion.

    Reference: economyA.c :: upd_consume()

    Army starvation: if a nation cannot feed its armies, PSTARVE% die per army.
    """
    # Army upkeep
    for army in armies:
        if not army.is_active or army.strength <= 0:
            continue

        ntn = nations.get(army.nation_id)
        if ntn is None:
            continue

        cost = compute_army_upkeep(army.unit_type, army.strength, army.supply)

        # Check if nation can afford food
        if ntn.res_food >= cost.food:
            ntn.deduct_resources(cost)
        else:
            # Starvation: army loses PSTARVE% of strength
            deaths = army.strength * PSTARVE // 100
            army.strength = max(0, army.strength - deaths)
            log.army_starvation[army.id] = deaths
            log.messages.append(
                f"Army {army.id} for nation {army.nation_id} starves: {deaths} deaths"
            )
            # Deduct whatever food is available
            ntn.res_food = 0

        if army.strength <= 0:
            army.is_active = False

    # Navy upkeep
    for navy in navies:
        if not navy.is_active:
            continue

        ntn = nations.get(navy.nation_id)
        if ntn is None:
            continue

        cost = compute_navy_upkeep(navy.crew, navy.supply)
        ntn.deduct_resources(cost)

    # Caravan upkeep
    for cvn in caravans:
        if not cvn.is_active:
            continue

        ntn = nations.get(cvn.nation_id)
        if ntn is None:
            continue

        cost = compute_caravan_upkeep(cvn.size)
        ntn.deduct_resources(cost)


# ---------------------------------------------------------------------------
# Phase 3 — Magic regen
# ---------------------------------------------------------------------------

def upd_magic(
    nations: dict[object, NationState],
    log: TurnLog,
) -> None:
    """
    Regenerate magic power for all nations; apply passive magic bonuses.

    Reference: magicX.c :: add_powers(), computeX.c passive bonuses
    """
    for nid, ntn in nations.items():
        new_mil, new_civ, new_wiz = regen_magic_power(
            current_military=ntn.power_military,
            current_civilian=ntn.power_civilian,
            current_wizardry=ntn.power_wizardry,
            attr_wiz_skill=ntn.attr_wiz_skill,
            attr_spell_pts=ntn.attr_spell_pts,
            race_traits=ntn.race_traits,
            shrines_owned=ntn.shrines_owned,
            player_class=ntn.player_class,
        )

        ntn.power_military = new_mil
        ntn.power_civilian = new_civ
        ntn.power_wizardry = new_wiz

        log.magic_regen[nid] = (new_mil, new_civ, new_wiz)

        # Apply passive bonuses (they're recorded in log for reporting; actual
        # production bonuses are handled in upd_sectors via adjust_production)
        bonuses = apply_passive_powers(new_mil, new_civ, new_wiz)
        if bonuses.get("morale_regen", 0) > 0:
            ntn.attr_morale = min(100, ntn.attr_morale + bonuses["morale_regen"])


# ---------------------------------------------------------------------------
# Phase 4 — Victory point computation (new system)
# ---------------------------------------------------------------------------

def upd_victory(
    nations: dict[object, NationState],
    sectors: list[SectorState],
    log: TurnLog,
) -> None:
    """
    Compute per-turn victory point accumulation.

    Victory conditions are class-specific (from the plan's Player Class table):
      - Empire Builder: points for territory, cities, population
      - Warlord: points for armies in enemy territory
      - Trader: points for trade routes (caravans active)
      - Theocrat: points for shrines controlled
      - etc.

    Default scoring: 1 VP per owned sector + bonus for capital.
    """
    # Count sectors per nation
    sector_counts: dict[object, int] = {}
    for sct in sectors:
        if sct.owner_nation_id is not None:
            sector_counts[sct.owner_nation_id] = sector_counts.get(sct.owner_nation_id, 0) + 1

    for nid, ntn in nations.items():
        vp = 0
        owned = sector_counts.get(nid, 0)

        cls = ntn.player_class.upper()
        if cls == "EMPIRE_BUILDER":
            vp += owned + ntn.shrines_owned
        elif cls == "THEOCRAT":
            vp += ntn.shrines_owned * 3
        elif cls == "WARLORD":
            vp += owned  # combat VPs handled in combat phase
        elif cls == "TRADER":
            vp += ntn.res_talons // 1000
        else:
            vp += owned  # default

        ntn.victory_points += vp


# ---------------------------------------------------------------------------
# Main turn entry point
# ---------------------------------------------------------------------------

def process_turn(
    turn: int,
    nations: dict[object, NationState],
    sectors: list[SectorState],
    armies: list[ArmyState] | None = None,
    navies: list[NavyState] | None = None,
    caravans: list[CaravanState] | None = None,
) -> TurnLog:
    """
    Process a complete game turn.

    Reference: executeX.c :: execute_turn()

    Returns a TurnLog describing what happened this turn.
    Caller is responsible for persisting state changes to the database.
    """
    log = TurnLog(turn=turn)
    armies = armies or []
    navies = navies or []
    caravans = caravans or []

    log.messages.append(f"--- Turn {turn} begin ---")

    # Phase 1: Sector production
    upd_sectors(nations, sectors, turn, log)
    log.messages.append("Sector production complete")

    # Phase 2: Military upkeep
    upd_consume(nations, armies, navies, caravans, log)
    log.messages.append("Unit upkeep applied")

    # Phase 3: Army/navy movement and combat (Phase 3 feature — stub)
    # upd_armies(nations, sectors, armies, log)
    # upd_navies(nations, sectors, navies, log)
    # upd_caravans(nations, sectors, caravans, log)

    # Phase 4: Magic regeneration
    upd_magic(nations, log)
    log.messages.append("Magic regenerated")

    # Phase 5: World events (Phase 3 feature — stub)
    # upd_events(nations, sectors, log)

    # Phase 6: Victory points
    upd_victory(nations, sectors, log)
    log.messages.append(f"--- Turn {turn} complete ---")

    return log
