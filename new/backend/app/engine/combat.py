"""
Combat engine — translates combatA.c logic to Python.

Reference: gpl-release/Src/combatA.c

Combat model:
- Attacker and defender roll num_dice d100 dice each
- Damage applied when roll exceeds damage_limit threshold
- Unit properties (UP_BALLISTICS, UP_ARROWWEAK, etc.) modify rolls
- Fortification reduces damage to defenders

Phase 1: stubs with type signatures.
Phase 2: full implementation.
"""

import random
from dataclasses import dataclass


@dataclass
class Combatant:
    strength: int
    attack_bonus: int
    defense_bonus: int
    efficiency: int
    unit_type: int
    is_fortified: bool = False
    fortress_level: int = 0


@dataclass
class CombatResult:
    attacker_losses: int
    defender_losses: int
    attacker_wins: bool
    rounds: int


def resolve_combat(
    attacker: Combatant,
    defender: Combatant,
    num_dice: int = 2,
    avg_damage: int = 50,
    damage_limit: int = 30,
    overmatch_adj: int = 10,
    min_damage_pct: int = 10,
) -> CombatResult:
    """
    Resolve one round of combat between two units.

    Reference: combatA.c :: do_combat()

    The original uses dice rolls scaled by relative strength (overmatch_adj
    applies when one side has > 2× the men of the other).

    Phase 2 TODO: port exact dice math from C, including:
    - UP_BALLISTICS / UP_ARROWWEAK interaction
    - UP_FORTDAMAGE for siege units
    - Fortification damage reduction
    - Morale effect on combat effectiveness
    """
    raise NotImplementedError("Phase 2")


def compute_capture_chance(
    attacker_strength: int,
    sector_efficiency: int,
    unit_capture_value: int,
) -> float:
    """
    Probability that an army captures a sector rather than just winning combat.

    Reference: combatA.c :: capture_check()
    """
    raise NotImplementedError("Phase 2")
