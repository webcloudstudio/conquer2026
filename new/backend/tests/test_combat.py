"""
Unit tests for the combat engine.

Cross-reference: gpl-release/Src/combatA.c
"""

import random

import pytest

from app.engine.combat import (
    Combatant,
    CombatResult,
    attempt_capture,
    combat_roll,
    compute_capture_chance,
    resolve_battle,
    resolve_combat,
)


def _c(strength: int, eff: int = 100, **kwargs) -> Combatant:
    return Combatant(strength=strength, attack_bonus=0, defense_bonus=0,
                     efficiency=eff, unit_type=0, **kwargs)


# ---------------------------------------------------------------------------
# Dice / roll
# ---------------------------------------------------------------------------

def test_combat_roll_range():
    """combat_roll() should always return a value in [0, 100]."""
    rng = random.Random(42)
    for _ in range(1000):
        r = combat_roll(rng)
        assert 0 <= r <= 100


def test_combat_roll_distribution():
    """combat_roll() mean should be close to 50 (normal distribution)."""
    rng = random.Random(0)
    rolls = [combat_roll(rng) for _ in range(10000)]
    mean = sum(rolls) / len(rolls)
    assert 40 <= mean <= 60   # within 10 points of 50


# ---------------------------------------------------------------------------
# Single-round combat
# ---------------------------------------------------------------------------

def test_zero_strength_attacker_raises():
    with pytest.raises(ValueError):
        resolve_combat(attacker=_c(0, eff=0), defender=_c(1000))


def test_combat_result_structure():
    """resolve_combat returns a valid CombatResult."""
    rng = random.Random(1)
    result = resolve_combat(attacker=_c(1000), defender=_c(1000), rng=rng)
    assert isinstance(result, CombatResult)
    assert result.attacker_losses >= 0
    assert result.defender_losses >= 0
    assert isinstance(result.attacker_wins, bool)


def test_losses_do_not_exceed_strength():
    """Neither side can lose more than their full strength."""
    rng = random.Random(7)
    result = resolve_combat(attacker=_c(500), defender=_c(300), rng=rng)
    assert result.attacker_losses <= 500
    assert result.defender_losses <= 300


# ---------------------------------------------------------------------------
# Battle (multi-round)
# ---------------------------------------------------------------------------

def test_stronger_attacker_wins_more_often():
    """A 10:1 strength advantage should yield high win rate over many battles."""
    rng = random.Random(42)
    wins = 0
    trials = 200
    for _ in range(trials):
        result = resolve_battle(attacker=_c(10000), defender=_c(1000), rng=rng)
        if result.attacker_wins:
            wins += 1
    win_rate = wins / trials
    assert win_rate >= 0.80, f"Expected ≥80% win rate, got {win_rate:.0%}"


def test_fortress_reduces_attacker_damage():
    """A fortified defender should take fewer losses than an unfortified one."""
    rng_open = random.Random(99)
    rng_fort = random.Random(99)

    result_open = resolve_combat(
        attacker=_c(1000),
        defender=_c(1000, is_fortified=False, fortress_level=0),
        rng=rng_open,
    )
    result_fort = resolve_combat(
        attacker=_c(1000),
        defender=_c(1000, is_fortified=True, fortress_level=24),
        rng=rng_fort,
    )
    # Fortified defender should take fewer losses (or at most equal)
    assert result_fort.defender_losses <= result_open.defender_losses


def test_equal_armies_mixed_outcome():
    """Equal armies should produce mixed win/loss results."""
    rng = random.Random(5)
    wins = sum(
        1 for _ in range(100)
        if resolve_combat(attacker=_c(1000), defender=_c(1000), rng=rng).attacker_wins
    )
    # Neither side should dominate completely
    assert 20 <= wins <= 80


# ---------------------------------------------------------------------------
# Capture
# ---------------------------------------------------------------------------

def test_capture_chance_range():
    """Capture probability should always be in [0, 1]."""
    for strength in [0, 100, 10000]:
        for eff in [0, 50, 100]:
            for ucv in [0, 50, 100]:
                p = compute_capture_chance(strength, eff, ucv)
                assert 0.0 <= p <= 1.0


def test_zero_attacker_no_capture():
    assert compute_capture_chance(0, 50, 80) == 0.0


def test_high_sector_efficiency_resists_capture():
    """High-efficiency sectors should be harder to capture."""
    low_eff = compute_capture_chance(1000, 10, 80)
    high_eff = compute_capture_chance(1000, 90, 80)
    assert high_eff <= low_eff


def test_attempt_capture_reduces_efficiency():
    """A successful capture should reduce sector efficiency."""
    rng = random.Random(0)
    # Force success by using a unit_capture_value that guarantees capture
    result = attempt_capture(
        attacker_strength=10000,
        sector_efficiency=60,
        unit_capture_value=100,
        rng=rng,
    )
    if result.captured:
        assert result.new_efficiency < 60
