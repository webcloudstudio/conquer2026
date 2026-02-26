"""
Unit tests for the combat engine.

Phase 1: stubs. All game-logic tests are xfail until Phase 2.
Cross-reference: gpl-release/Src/combatA.c
"""

import pytest
from app.engine.combat import Combatant, resolve_combat


@pytest.mark.xfail(reason="Phase 2: engine not yet implemented", strict=True)
def test_stronger_attacker_wins_more_often():
    """A 10:1 strength advantage should yield high win rate."""
    wins = 0
    for _ in range(100):
        result = resolve_combat(
            attacker=Combatant(strength=10000, attack_bonus=0, defense_bonus=0, efficiency=100, unit_type=0),
            defender=Combatant(strength=1000, attack_bonus=0, defense_bonus=0, efficiency=100, unit_type=0),
        )
        if result.attacker_wins:
            wins += 1
    assert wins >= 85  # at least 85% win rate for 10:1


@pytest.mark.xfail(reason="Phase 2: engine not yet implemented", strict=True)
def test_fortress_reduces_attacker_damage():
    """Fortification should reduce attacker damage to the defending unit."""
    result_open = resolve_combat(
        attacker=Combatant(strength=1000, attack_bonus=0, defense_bonus=0, efficiency=100, unit_type=0),
        defender=Combatant(strength=1000, attack_bonus=0, defense_bonus=0, efficiency=100, unit_type=0,
                           is_fortified=False, fortress_level=0),
    )
    result_fort = resolve_combat(
        attacker=Combatant(strength=1000, attack_bonus=0, defense_bonus=0, efficiency=100, unit_type=0),
        defender=Combatant(strength=1000, attack_bonus=0, defense_bonus=0, efficiency=100, unit_type=0,
                           is_fortified=True, fortress_level=50),
    )
    # Fortified defender should take fewer losses
    assert result_fort.defender_losses < result_open.defender_losses


@pytest.mark.xfail(reason="Phase 2: engine not yet implemented", strict=True)
def test_zero_strength_cannot_attack():
    with pytest.raises(ValueError):
        resolve_combat(
            attacker=Combatant(strength=0, attack_bonus=0, defense_bonus=0, efficiency=0, unit_type=0),
            defender=Combatant(strength=1000, attack_bonus=0, defense_bonus=0, efficiency=100, unit_type=0),
        )
