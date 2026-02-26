"""
Combat engine — translates combatA.c logic to Python.

Reference: gpl-release/Src/combatA.c

Combat model (mirrors C original):
  - Each side rolls NUMDICE dice, each die is in range [0, cb_dicelimit).
  - Sum is scaled to 0–100 → combat_roll().
  - If attacker roll > DAMAGE_LIMIT → defender takes damage equal to (roll - DAMAGE_LIMIT).
  - If defender roll > DAMAGE_LIMIT → attacker takes damage.
  - Overmatch: when one side has >2× the strength, the weaker side's damage
    is reduced by OVERMATCH_ADJ percentage points.
  - Fortification reduces incoming damage to the defender.
  - Minimum damage per engagement: PMINDAMAGE%.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Global combat constants — from header.h.dist
# ---------------------------------------------------------------------------
NUMDICE: int = 10        # number of dice per roll
DAMAGE_LIMIT: int = 50   # roll must exceed this to deal damage
AVG_DAMAGE: int = 50     # baseline average damage roll
OVERMATCH_ADJ: int = 10  # penalty when outnumbered >2:1
PMINDAMAGE: int = 5      # minimum damage % per combat round

# Fortification caps (MAXFORTVAL from header.h.dist)
_MAXFORTVAL: int = 24
# Max damage reduction from fortification
_MAX_FORT_REDUCTION: int = 40  # percentage points


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Combatant:
    strength: int          # men / monsters / ships
    attack_bonus: int      # flat attack modifier (0–100 scale)
    defense_bonus: int     # flat defense modifier
    efficiency: int        # 0–100; scales combat effectiveness
    unit_type: int         # 0=normal army, 1=spellcaster, 2=monster, 3=navy
    is_fortified: bool = False
    fortress_level: int = 0  # 0–MAXFORTVAL; reduces incoming damage


@dataclass
class CombatResult:
    attacker_losses: int
    defender_losses: int
    attacker_wins: bool
    rounds: int
    attacker_damage_dealt: int = 0   # % damage dealt to defender
    defender_damage_dealt: int = 0   # % damage dealt to attacker


@dataclass
class CaptureResult:
    captured: bool
    new_efficiency: int


# ---------------------------------------------------------------------------
# Dice / roll functions — mirrors combatA.c :: init_combat_roll() / combat_roll()
# ---------------------------------------------------------------------------

def _init_roll_params(numdice: int = NUMDICE) -> tuple[int, int]:
    """
    Return (cb_boundary, cb_dicelimit) that make rolls evenly map to 0–100.

    Reference: combatA.c :: init_combat_roll()
    """
    cb_boundary = 100
    while cb_boundary % numdice != 0:
        cb_boundary += 100
    cb_dicelimit = cb_boundary // numdice + 1
    return cb_boundary, cb_dicelimit


_CB_BOUNDARY, _CB_DICELIMIT = _init_roll_params()


def combat_roll(rng: random.Random | None = None) -> int:
    """
    Generate a single combat roll in the range [0, 100].

    Reference: combatA.c :: combat_roll()
    """
    r = rng or random
    hold = sum(r.randint(0, _CB_DICELIMIT - 1) for _ in range(NUMDICE))
    return (100 * hold) // _CB_BOUNDARY


# ---------------------------------------------------------------------------
# Core combat resolution
# ---------------------------------------------------------------------------

def resolve_combat(
    attacker: Combatant,
    defender: Combatant,
    num_dice: int = NUMDICE,
    avg_damage: int = AVG_DAMAGE,
    damage_limit: int = DAMAGE_LIMIT,
    overmatch_adj: int = OVERMATCH_ADJ,
    min_damage_pct: int = PMINDAMAGE,
    rng: random.Random | None = None,
) -> CombatResult:
    """
    Resolve one round of combat between two units.

    Reference: combatA.c :: do_combat()

    Returns CombatResult with absolute losses and winner flag.
    """
    if attacker.strength <= 0:
        raise ValueError("Attacker has zero strength; cannot initiate combat.")
    if defender.strength <= 0:
        raise ValueError("Defender has zero strength.")

    r = rng or random

    # Efficiency scales effective strength (0–100)
    eff_a = max(1, attacker.efficiency) / 100.0
    eff_d = max(1, defender.efficiency) / 100.0
    eff_str_a = max(1, int(attacker.strength * eff_a))
    eff_str_d = max(1, int(defender.strength * eff_d))

    # Roll dice for both sides
    atk_roll = combat_roll(r) + attacker.attack_bonus
    def_roll = combat_roll(r) + defender.defense_bonus

    atk_roll = max(0, min(100, atk_roll))
    def_roll = max(0, min(100, def_roll))

    # Overmatch: if one side has >2× effective strength, the weaker side is penalised
    if eff_str_a >= eff_str_d * 2:
        def_roll = max(0, def_roll - overmatch_adj)
    elif eff_str_d >= eff_str_a * 2:
        atk_roll = max(0, atk_roll - overmatch_adj)

    # Compute raw damage percentages (must exceed damage_limit to hurt)
    atk_raw = atk_roll - damage_limit if atk_roll > damage_limit else 0
    def_raw = def_roll - damage_limit if def_roll > damage_limit else 0
    atk_damage_pct = max(min_damage_pct, atk_raw)
    def_damage_pct = max(min_damage_pct, def_raw)

    # Fortification: reduces damage to defender
    if defender.is_fortified and defender.fortress_level > 0:
        fort_reduction = min(
            _MAX_FORT_REDUCTION,
            int(defender.fortress_level / _MAXFORTVAL * _MAX_FORT_REDUCTION),
        )
        atk_damage_pct = max(min_damage_pct, atk_damage_pct - fort_reduction)

    # Apply damage to both sides
    # deaths = (strength * damage_pct) / 100  (from combatA.c damage_unit())
    defender_losses = (defender.strength * atk_damage_pct) // 100
    attacker_losses = (attacker.strength * def_damage_pct) // 100

    attacker_wins = (atk_roll > def_roll) or (attacker_losses < defender_losses)

    return CombatResult(
        attacker_losses=attacker_losses,
        defender_losses=defender_losses,
        attacker_wins=attacker_wins,
        rounds=1,
        attacker_damage_dealt=atk_damage_pct,
        defender_damage_dealt=def_damage_pct,
    )


# ---------------------------------------------------------------------------
# Multi-round battle
# ---------------------------------------------------------------------------

def resolve_battle(
    attacker: Combatant,
    defender: Combatant,
    max_rounds: int = 10,
    rng: random.Random | None = None,
) -> CombatResult:
    """
    Run multiple rounds until one side is wiped out or max_rounds reached.

    Returns aggregate CombatResult with total losses.
    """
    if attacker.strength <= 0:
        raise ValueError("Attacker has zero strength.")
    if defender.strength <= 0:
        raise ValueError("Defender has zero strength.")

    r = rng or random

    # Work with mutable copies of strength
    atk = Combatant(**attacker.__dict__)
    defn = Combatant(**defender.__dict__)

    total_atk_loss = 0
    total_def_loss = 0
    final_round = 0

    for rnd in range(max_rounds):
        if atk.strength <= 0 or defn.strength <= 0:
            break

        result = resolve_combat(atk, defn, rng=r)
        total_atk_loss += result.attacker_losses
        total_def_loss += result.defender_losses
        final_round = rnd + 1

        atk.strength -= result.attacker_losses
        defn.strength -= result.defender_losses

    attacker_wins = defn.strength <= 0 or (atk.strength > defn.strength)

    return CombatResult(
        attacker_losses=total_atk_loss,
        defender_losses=total_def_loss,
        attacker_wins=attacker_wins,
        rounds=final_round,
    )


# ---------------------------------------------------------------------------
# Sector capture
# ---------------------------------------------------------------------------

def compute_capture_chance(
    attacker_strength: int,
    sector_efficiency: int,
    unit_capture_value: int,
) -> float:
    """
    Probability that an army captures a sector rather than just winning combat.

    Reference: combatA.c :: capture_check()

    Higher attacker strength and lower sector efficiency increase odds.
    unit_capture_value is a unit property (0–100) from ainfo_list.
    """
    if attacker_strength <= 0:
        return 0.0

    # Base capture chance proportional to unit capability
    base_chance = unit_capture_value / 100.0

    # Sector resistance: high-efficiency sectors are harder to capture
    resistance = max(0.0, sector_efficiency / 100.0)

    chance = base_chance * (1.0 - resistance * 0.5)
    return max(0.0, min(1.0, chance))


def attempt_capture(
    attacker_strength: int,
    sector_efficiency: int,
    unit_capture_value: int,
    rng: random.Random | None = None,
) -> CaptureResult:
    """
    Roll against capture chance; return result and new sector efficiency.

    On successful capture, sector efficiency drops to 10–30% (transition cost).
    """
    r = rng or random
    chance = compute_capture_chance(attacker_strength, sector_efficiency, unit_capture_value)
    captured = r.random() < chance

    if captured:
        new_eff = max(10, sector_efficiency // 3)
    else:
        new_eff = sector_efficiency

    return CaptureResult(captured=captured, new_efficiency=new_eff)
