"""Tests for the NPC AI engine."""

import random

from app.engine.npc_ai import (
    NpcArmy,
    NpcNation,
    NpcSector,
    run_npc_turn,
)


def _make_sectors(n: int = 10):
    """Build a small linear map of land sectors."""
    return [
        NpcSector(x=i, y=0, altitude=2, designation=0, efficiency=60,
                  population=5000, minerals=0, owner_nation_id=None)
        for i in range(n)
    ]


def test_npc_expands_to_adjacent_unclaimed():
    """NPC army should move to claim adjacent unclaimed sector."""
    nation = NpcNation(id="n1", player_class="WARLORD")
    army = NpcArmy(id="a1", nation_id="n1", strength=2000, efficiency=80, movement=4, x=0, y=0)
    sectors = _make_sectors(5)
    sectors[0].owner_nation_id = "n1"  # army's current sector owned

    result = run_npc_turn(nation, [army], sectors, [], rng=random.Random(42))
    moves = [o for o in result.orders if o.kind == "move"]
    assert len(moves) >= 1
    assert moves[0].army_id == "a1"


def test_npc_attacks_weaker_enemy():
    """NPC should attack if adjacent enemy has 80% of our strength."""
    nation = NpcNation(id="n1", player_class="WARLORD")
    army = NpcArmy(id="a1", nation_id="n1", strength=2000, efficiency=80, movement=4, x=0, y=0)
    enemy_army = NpcArmy(
        id="a2", nation_id="n2", strength=1000, efficiency=80, movement=4, x=1, y=0
    )
    sectors = _make_sectors(5)

    result = run_npc_turn(nation, [army], sectors, [army, enemy_army], rng=random.Random(42))
    attacks = [o for o in result.orders if o.kind == "attack"]
    assert len(attacks) >= 1
    assert attacks[0].x == 1 and attacks[0].y == 0


def test_npc_does_not_attack_stronger_enemy():
    """NPC should not attack if enemy is much stronger."""
    nation = NpcNation(id="n1", player_class="WARLORD")
    army = NpcArmy(id="a1", nation_id="n1", strength=500, efficiency=80, movement=4, x=0, y=0)
    enemy = NpcArmy(id="a2", nation_id="n2", strength=5000, efficiency=80, movement=4, x=1, y=0)
    sectors = _make_sectors(5)

    result = run_npc_turn(nation, [army], sectors, [army, enemy], rng=random.Random(42))
    attacks = [o for o in result.orders if o.kind == "attack"]
    assert len(attacks) == 0


def test_npc_designates_mine_for_mineral_sector():
    """NPC should designate high-mineral owned sectors as mines."""
    nation = NpcNation(id="n1", player_class="WARLORD")
    sectors = _make_sectors(3)
    sectors[0].owner_nation_id = "n1"
    sectors[0].minerals = 8  # high mineral count

    result = run_npc_turn(nation, [], sectors, [], rng=random.Random(42))
    designates = [o for o in result.orders if o.kind == "designate" and o.designation == 2]
    assert len(designates) >= 1


def test_npc_designates_farm_for_lowland():
    """NPC should designate low-altitude owned sectors as farms."""
    nation = NpcNation(id="n1", player_class="WARLORD")
    sectors = [NpcSector(x=0, y=0, altitude=1, designation=0, efficiency=60, population=5000,
                         minerals=0, owner_nation_id="n1")]

    result = run_npc_turn(nation, [], sectors, [], rng=random.Random(42))
    farms = [o for o in result.orders if o.kind == "designate" and o.designation == 1]
    assert len(farms) >= 1


def test_npc_no_orders_empty_nation():
    """Empty nation with no armies or sectors produces no orders."""
    nation = NpcNation(id="n1", player_class="WARLORD")
    result = run_npc_turn(nation, [], [], [], rng=random.Random(42))
    assert result.orders == []
