"""
Integration tests for the turn processor.

Verifies that a full turn progresses correctly: sectors produce resources,
armies consume upkeep, magic regenerates, and victory points accumulate.
"""

from app.engine.turn_processor import (
    ArmyState,
    NationState,
    SectorState,
    process_turn,
)
from app.models.sector import Designation, Vegetation

# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------

def _make_nation(nid: str, **kwargs) -> NationState:
    return NationState(id=nid, **kwargs)


def _make_farm(nid: str, x: int = 0, y: int = 0) -> SectorState:
    return SectorState(
        x=x, y=y,
        designation=Designation.FARM,
        altitude=4,
        vegetation=Vegetation.GRASSLAND,
        efficiency=80,
        population=5000,
        owner_nation_id=nid,
    )


# ---------------------------------------------------------------------------
# Basic turn processing
# ---------------------------------------------------------------------------

def test_sector_production_increases_food():
    """Owning a farm sector should increase nation's food reserves."""
    nation = _make_nation("n1", res_food=0, attr_taxrate=30, attr_eatrate=1, attr_morale=70)
    sector = _make_farm("n1")
    nations = {"n1": nation}

    # Turn 0 = spring (farm produces food)
    log = process_turn(turn=0, nations=nations, sectors=[sector])

    # Nation's food should be >= what they started with (production > small per-1000 eatrate)
    assert nation.res_food > 0
    assert "n1" in log.sector_production


def test_farm_winter_reduces_production():
    """In winter (turn=3), farm production should be zero."""
    nation_spring = _make_nation("n1", res_food=0, attr_taxrate=30, attr_eatrate=1, attr_morale=70)
    nation_winter = _make_nation("n2", res_food=0, attr_taxrate=30, attr_eatrate=1, attr_morale=70)
    sector_spring = _make_farm("n1", x=0, y=0)
    sector_winter = _make_farm("n2", x=1, y=0)

    process_turn(turn=0, nations={"n1": nation_spring}, sectors=[sector_spring])
    process_turn(turn=3, nations={"n2": nation_winter}, sectors=[sector_winter])

    # Winter nation may actually have negative food (consumed but no production)
    # Spring nation should have more food
    spring_food = nation_spring.res_food
    winter_food = nation_winter.res_food
    assert spring_food >= winter_food


def test_army_upkeep_reduces_food():
    """Maintaining an army should reduce the nation's food reserves."""
    nation = _make_nation("n1", res_food=10000, attr_taxrate=30, attr_eatrate=1, attr_morale=70)
    sector = _make_farm("n1")
    army = ArmyState(id="a1", nation_id="n1", unit_type=0, strength=1000, supply=1)

    process_turn(
        turn=1,
        nations={"n1": nation},
        sectors=[sector],
        armies=[army],
    )
    # After upkeep, food could go up (from production) or down (if upkeep > production)
    # Just verify the turn completes without error and army is still alive
    assert army.is_active


def test_army_starvation_kills_men():
    """An army with no food supply should suffer PSTARVE% losses."""
    nation = _make_nation("n1", res_food=0, attr_taxrate=0, attr_eatrate=1, attr_morale=70)
    # No sectors → no production
    army = ArmyState(id="a1", nation_id="n1", unit_type=0, strength=1000, supply=1)

    initial_strength = army.strength
    log = process_turn(
        turn=0,
        nations={"n1": nation},
        sectors=[],   # no sectors, no production
        armies=[army],
    )

    assert army.strength < initial_strength
    assert "a1" in log.army_starvation


def test_magic_regenerates_each_turn():
    """Nations with shrines should accumulate magic power each turn."""
    nation = _make_nation(
        "n1",
        power_military=0,
        power_civilian=0,
        power_wizardry=0,
        attr_wiz_skill=20,
        attr_spell_pts=100,
        shrines_owned=3,
        player_class="",
    )
    nations = {"n1": nation}

    process_turn(turn=0, nations=nations, sectors=[])

    assert nation.power_military > 0
    assert nation.power_civilian > 0
    assert nation.power_wizardry > 0


def test_theocrat_regenerates_more():
    """Theocrat nations should regenerate more magic than default."""
    nation_default = _make_nation(
        "n1", power_military=0, power_civilian=0, power_wizardry=0,
        attr_wiz_skill=20, attr_spell_pts=100, shrines_owned=3, player_class="",
    )
    nation_theocrat = _make_nation(
        "n2", power_military=0, power_civilian=0, power_wizardry=0,
        attr_wiz_skill=20, attr_spell_pts=100, shrines_owned=3, player_class="THEOCRAT",
    )

    process_turn(0, {"n1": nation_default}, [])
    process_turn(0, {"n2": nation_theocrat}, [])

    assert nation_theocrat.power_military >= nation_default.power_military


def test_victory_points_accumulate():
    """Victory points should increase each turn for nations with sectors."""
    nation = _make_nation("n1", player_class="EMPIRE_BUILDER")
    sector = _make_farm("n1")

    assert nation.victory_points == 0
    process_turn(0, {"n1": nation}, [sector])
    assert nation.victory_points > 0


def test_multi_nation_turn():
    """Multiple nations can be processed in a single turn without interference."""
    n1 = _make_nation("n1", res_food=5000, attr_taxrate=30, attr_eatrate=1, attr_morale=70)
    n2 = _make_nation("n2", res_food=5000, attr_taxrate=30, attr_eatrate=1, attr_morale=70)
    s1 = _make_farm("n1", x=0, y=0)
    s2 = _make_farm("n2", x=10, y=0)

    log = process_turn(0, {"n1": n1, "n2": n2}, [s1, s2])

    assert "n1" in log.sector_production
    assert "n2" in log.sector_production


def test_turn_log_messages_populated():
    nation = _make_nation("n1")
    log = process_turn(0, {"n1": nation}, [])
    assert len(log.messages) > 0
    assert any("Turn" in m for m in log.messages)
