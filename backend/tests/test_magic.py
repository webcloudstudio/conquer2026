"""
Unit tests for the magic engine.

Cross-reference: gpl-release/Src/magicA.c, gpl-release/Src/magicX.c,
                 gpl-release/Include/spellsX.h
"""

import random

import pytest

from app.engine.magic import (
    SPELL_COSTS,
    SPL_STR_LIM,
    CivilianPower,
    MilitaryPower,
    Spell,
    WizardryPower,
    apply_passive_powers,
    can_cast,
    cast_spell,
    regen_magic_power,
)

# ---------------------------------------------------------------------------
# Spell cost sanity
# ---------------------------------------------------------------------------

def test_all_spells_have_cost():
    for spell in Spell:
        assert spell in SPELL_COSTS
        assert SPELL_COSTS[spell] > 0


# ---------------------------------------------------------------------------
# can_cast — eligibility checks
# ---------------------------------------------------------------------------

def test_insufficient_spell_points():
    assert not can_cast(
        spell=Spell.SUMMON,
        caster_spell_points=1,
        power_military=10,
        power_civilian=0,
        power_wizardry=10,
        is_full_caster=True,
    )


def test_low_strength_cannot_cast():
    assert not can_cast(
        spell=Spell.COMBAT,
        caster_spell_points=50,
        power_military=10,
        power_civilian=0,
        power_wizardry=0,
        caster_strength=SPL_STR_LIM - 1,
    )


def test_full_strength_can_cast():
    assert can_cast(
        spell=Spell.COMBAT,
        caster_spell_points=50,
        power_military=10,
        power_civilian=0,
        power_wizardry=0,
        is_full_caster=True,
        caster_strength=100,
    )


def test_monster_cannot_cast_restricted_spell():
    """Quake is SI_NONMONSTER; monsters cannot cast it."""
    assert not can_cast(
        spell=Spell.QUAKE,
        caster_spell_points=50,
        power_military=0,
        power_civilian=0,
        power_wizardry=15,
        is_full_caster=True,
        is_monster=True,
    )


def test_insufficient_magic_power():
    """Quake requires wizardry power ≥ 10."""
    assert not can_cast(
        spell=Spell.QUAKE,
        caster_spell_points=50,
        power_military=0,
        power_civilian=0,
        power_wizardry=5,   # need 10
        is_full_caster=True,
        is_monster=False,
    )


def test_anycast_spell_no_caster_required():
    """SENDING can be cast by any unit with enough spell points."""
    assert can_cast(
        spell=Spell.SENDING,
        caster_spell_points=10,
        power_military=0,
        power_civilian=5,
        power_wizardry=0,
        is_full_caster=False,
        is_spellcaster=False,
        is_monster=False,
        caster_strength=60,
    )


# ---------------------------------------------------------------------------
# cast_spell
# ---------------------------------------------------------------------------

def test_cast_spell_insufficient_points_fails():
    result = cast_spell(Spell.SUMMON, caster_spell_points=0, target_x=5, target_y=5)
    assert not result.success


def test_cast_spell_returns_sp_cost_on_success():
    rng = random.Random(1)
    # Heal has 85% success; seed 1 should succeed within a few retries
    for seed in range(100):
        rng = random.Random(seed)
        result = cast_spell(Spell.HEAL, caster_spell_points=50, target_x=0, target_y=0,
                            rng=rng, target_strength=1000)
        if result.success:
            assert result.effects.get("sp_cost", 0) == SPELL_COSTS[Spell.HEAL]
            assert result.effects.get("heal_amount", 0) > 0
            break
    else:
        pytest.fail("HEAL never succeeded in 100 seeds")


def test_quake_spell_effects():
    rng = random.Random(0)
    for seed in range(200):
        rng = random.Random(seed)
        result = cast_spell(Spell.QUAKE, caster_spell_points=50, target_x=10, target_y=10, rng=rng)
        if result.success:
            assert "fortress_damage" in result.effects
            assert "pop_damage_pct" in result.effects
            break
    else:
        pytest.fail("QUAKE never succeeded in 200 seeds")


# ---------------------------------------------------------------------------
# regen_magic_power
# ---------------------------------------------------------------------------

def test_regen_increases_power():
    new_mil, new_civ, new_wiz = regen_magic_power(
        current_military=5,
        current_civilian=5,
        current_wizardry=5,
        attr_wiz_skill=20,
        attr_spell_pts=100,
        race_traits=0,
        shrines_owned=2,
        player_class="",
    )
    assert new_mil > 5
    assert new_civ > 5
    assert new_wiz > 5


def test_theocrat_regen_higher():
    """Theocrat should regenerate more magic than a default nation."""
    normal = regen_magic_power(5, 5, 5, 20, 100, 0, 2, player_class="")
    theocrat = regen_magic_power(5, 5, 5, 20, 100, 0, 2, player_class="THEOCRAT")
    assert all(t >= n for t, n in zip(theocrat, normal))


def test_power_capped_at_spell_pts():
    """Power levels should not exceed attr_spell_pts."""
    new_mil, new_civ, new_wiz = regen_magic_power(
        current_military=99,
        current_civilian=99,
        current_wizardry=99,
        attr_wiz_skill=100,
        attr_spell_pts=100,
        race_traits=0,
        shrines_owned=10,
        player_class="",
    )
    assert new_mil <= 100
    assert new_civ <= 100
    assert new_wiz <= 100


def test_zero_shrines_no_shrine_regen():
    """With zero shrines and no wiz_skill, regen should be minimal."""
    new_mil, new_civ, new_wiz = regen_magic_power(
        current_military=0,
        current_civilian=0,
        current_wizardry=0,
        attr_wiz_skill=0,
        attr_spell_pts=100,
        race_traits=0,
        shrines_owned=0,
        player_class="",
    )
    assert new_mil == 0
    assert new_civ == 0
    assert new_wiz == 0


# ---------------------------------------------------------------------------
# Passive powers
# ---------------------------------------------------------------------------

def test_farming_passive_boosts_food():
    bonuses = apply_passive_powers(
        military_power=0,
        civilian_power=int(CivilianPower.FARMING),
        wizardry_power=0,
    )
    assert bonuses["food_pct"] > 100


def test_druidism_passive_boosts_wood():
    bonuses = apply_passive_powers(
        military_power=0,
        civilian_power=0,
        wizardry_power=int(WizardryPower.DRUIDISM),
    )
    assert bonuses["wood_pct"] > 100


def test_terror_passive_penalises_enemy():
    bonuses = apply_passive_powers(
        military_power=int(MilitaryPower.TERROR),
        civilian_power=0,
        wizardry_power=0,
    )
    assert bonuses["enemy_morale_penalty"] > 0
