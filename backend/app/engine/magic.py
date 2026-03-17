"""
Magic engine — translates magicA.c / magicX.c logic to Python.

Reference: gpl-release/Src/magicA.c, gpl-release/Src/magicX.c,
           gpl-release/Include/spellsX.h

Three power types (MAG_NUMBER=3): MILITARY, CIVILIAN, WIZARDRY
Each holds bitmask sub-powers that provide passive bonuses.

Ten spells (Spelltype enum in spellsX.h):
  COMBAT, FLIGHT, HEAL, QUAKE, SENDING, SCARE, SUMMON, TPORT, TRANSMUTE, TRANSFER

Caster requirements (from SI_* flags in spellsX.h):
  SI_ANYCAST   — any unit with spell_points
  SI_SPELLCASTER — must be a spellcaster unit
  SI_FULLCASTER  — must be a full mage (not partial)
  SI_NONMONSTER  — monsters cannot use this spell
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import IntEnum, IntFlag

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class Spell(IntEnum):
    COMBAT    = 0
    FLIGHT    = 1
    HEAL      = 2
    QUAKE     = 3
    SENDING   = 4
    SCARE     = 5
    SUMMON    = 6
    TPORT     = 7
    TRANSMUTE = 8
    TRANSFER  = 9


class MagicPower(IntEnum):
    MILITARY  = 0   # MAG_MILITARY — combat-related passive powers
    CIVILIAN  = 1   # MAG_CIVILIAN — economy/movement passive powers
    WIZARDRY  = 2   # MAG_WIZARDRY — active attack/defense spells


# ---------------------------------------------------------------------------
# Power sub-bitmasks (from magicX.h / computeX.c comments)
# ---------------------------------------------------------------------------

class MilitaryPower(IntFlag):
    NONE       = 0x00
    COMBAT_BON = 0x01   # MM_COMBAT  — +combat roll bonus to all armies
    GUARD      = 0x02   # MM_GUARD   — units resist capture
    TERROR     = 0x04   # MM_TERROR  — enemy armies −morale
    RALLY      = 0x08   # MM_RALLY   — morale regenerates faster


class CivilianPower(IntFlag):
    NONE       = 0x00
    FARMING    = 0x01   # MC_FARMING  — +20% food production
    MINER      = 0x02   # MC_MINER    — +20% jewels/metals
    HEALING    = 0x04   # MC_HEALING  — population grows faster
    SWIFT      = 0x08   # MC_SWIFT    — army movement +1


class WizardryPower(IntFlag):
    NONE       = 0x00
    EARTH      = 0x04   # MW_EARTH    — +10% metals
    DRUIDISM   = 0x08   # MW_DRUIDISM — +20% wood
    FIRE_ATK   = 0x10   # MW_FIREATK  — ranged combat attack bonus
    SHIELD     = 0x20   # MW_SHIELD   — reduces incoming damage


# ---------------------------------------------------------------------------
# Spell definitions — cost, drain, cast rate, caster requirements, power needs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SpellDef:
    name: str
    cost: int               # spell_points cost to cast
    drain: int              # caster strength drained (SPL_STR_LIM=50 minimum)
    rate: int               # % chance of success (1–100)
    need_fullcaster: bool   # SI_FULLCASTER
    need_caster: bool       # SI_SPELLCASTER
    nonmonster: bool        # SI_NONMONSTER
    anycast: bool           # SI_ANYCAST
    pow_need: tuple[int, int, int]   # minimum [military, civilian, wizardry] power


_SPELL_DEFS: dict[Spell, SpellDef] = {
    Spell.COMBAT: SpellDef(
        "Combat", cost=10, drain=10, rate=80,
        need_fullcaster=False, need_caster=True, nonmonster=False, anycast=False,
        pow_need=(5, 0, 0)),
    Spell.FLIGHT: SpellDef(
        "Flight", cost=8, drain=5, rate=70,
        need_fullcaster=False, need_caster=True, nonmonster=False, anycast=False,
        pow_need=(3, 3, 0)),
    Spell.HEAL: SpellDef(
        "Heal", cost=12, drain=8, rate=85,
        need_fullcaster=False, need_caster=True, nonmonster=False, anycast=True,
        pow_need=(0, 5, 0)),
    Spell.QUAKE: SpellDef(
        "Quake", cost=20, drain=15, rate=60,
        need_fullcaster=True, need_caster=True, nonmonster=True, anycast=False,
        pow_need=(0, 0, 10)),
    Spell.SENDING: SpellDef(
        "Sending", cost=5, drain=3, rate=90,
        need_fullcaster=False, need_caster=False, nonmonster=True, anycast=True,
        pow_need=(0, 2, 0)),
    Spell.SCARE: SpellDef(
        "Scare", cost=6, drain=4, rate=75,
        need_fullcaster=False, need_caster=True, nonmonster=False, anycast=False,
        pow_need=(3, 0, 0)),
    Spell.SUMMON: SpellDef(
        "Summon", cost=25, drain=20, rate=50,
        need_fullcaster=True, need_caster=True, nonmonster=True, anycast=False,
        pow_need=(5, 0, 10)),
    Spell.TPORT: SpellDef(
        "Tport", cost=15, drain=10, rate=65,
        need_fullcaster=True, need_caster=True, nonmonster=True, anycast=False,
        pow_need=(0, 5, 5)),
    Spell.TRANSMUTE: SpellDef(
        "Transmute", cost=18, drain=12, rate=55,
        need_fullcaster=True, need_caster=True, nonmonster=True, anycast=False,
        pow_need=(0, 5, 5)),
    Spell.TRANSFER: SpellDef(
        "Transfer", cost=10, drain=5, rate=80,
        need_fullcaster=False, need_caster=True, nonmonster=True, anycast=False,
        pow_need=(2, 2, 2)),
}

# Convenience accessor (backwards compat with stub that used SPELL_COSTS)
SPELL_COSTS: dict[Spell, int] = {s: d.cost for s, d in _SPELL_DEFS.items()}

# Spell strength limits from spellsX.h
SPL_STR_LIM: int = 50   # minimum strength to cast
SPL_STR_MIN: int = 20   # minimum strength remaining after casting


# ---------------------------------------------------------------------------
# Casting eligibility
# ---------------------------------------------------------------------------

def can_cast(
    spell: Spell,
    caster_spell_points: int,
    power_military: int,
    power_civilian: int,
    power_wizardry: int,
    is_full_caster: bool = False,
    is_spellcaster: bool = True,
    is_monster: bool = False,
    caster_strength: int = 100,
) -> bool:
    """
    Check whether a unit can cast a given spell.

    Reference: magicX.c :: can_cast_spell(), magic_ok()

    Checks:
      1. Caster has enough spell_points (>= spell cost).
      2. Caster strength is at or above SPL_STR_LIM.
      3. Unit type meets the spell's caster requirements.
      4. Nation has sufficient magic powers for the spell's pow_need.
    """
    sdef = _SPELL_DEFS[spell]

    # Strength gate
    if caster_strength < SPL_STR_LIM:
        return False

    # Spell point cost
    if caster_spell_points < sdef.cost:
        return False

    # Monster restriction
    if sdef.nonmonster and is_monster:
        return False

    # Caster type requirements
    if sdef.need_fullcaster and not is_full_caster:
        return False
    if sdef.need_caster and not (is_full_caster or is_spellcaster):
        return False

    # Magic power requirements
    mil_need, civ_need, wiz_need = sdef.pow_need
    if power_military < mil_need:
        return False
    if power_civilian < civ_need:
        return False
    if power_wizardry < wiz_need:
        return False

    return True


# ---------------------------------------------------------------------------
# Spell effects
# ---------------------------------------------------------------------------

@dataclass
class SpellResult:
    success: bool
    spell: Spell
    message: str
    effects: dict = field(default_factory=dict)   # effect key → value


def cast_spell(
    spell: Spell,
    caster_spell_points: int,
    target_x: int,
    target_y: int,
    rng: random.Random | None = None,
    **kwargs: object,
) -> SpellResult:
    """
    Execute a spell and return a SpellResult describing what happened.

    Reference: magicA.c :: cast_spell()

    The success roll uses sdef.rate (% chance), matching the C 'rand_val(100) < rate' pattern.
    kwargs may contain context such as target army/sector data for specific spells.
    """
    sdef = _SPELL_DEFS[spell]
    r = rng or random

    if caster_spell_points < sdef.cost:
        return SpellResult(
            success=False,
            spell=spell,
            message=f"Insufficient spell points (need {sdef.cost}, have {caster_spell_points})",
        )

    # Cast attempt
    roll = r.randint(0, 99)
    success = roll < sdef.rate

    if not success:
        return SpellResult(
            success=False,
            spell=spell,
            message=f"{sdef.name} fizzled (rolled {roll}, needed < {sdef.rate})",
            effects={"sp_cost": sdef.cost // 2},  # half cost on failure
        )

    effects: dict = {"sp_cost": sdef.cost, "str_drain": sdef.drain}

    # Spell-specific effects
    if spell == Spell.COMBAT:
        # +20 combat roll bonus for caster's army this turn
        effects["combat_bonus"] = 20

    elif spell == Spell.FLIGHT:
        # Target army gains flight status for 1 turn (+1 movement, ignores ZOC)
        effects["flight_turns"] = 1

    elif spell == Spell.HEAL:
        # Recover men/strength equal to 10% of original strength
        heal_pct = 10
        heal_amount = kwargs.get("target_strength", 0) * heal_pct // 100
        effects["heal_amount"] = int(heal_amount)

    elif spell == Spell.QUAKE:
        # Earthquake: reduce fortress level by 1d6 and population by 10–30%
        dmg = r.randint(1, 6)
        effects["fortress_damage"] = dmg
        effects["pop_damage_pct"] = r.randint(10, 30)

    elif spell == Spell.SENDING:
        # Message to another nation (cosmetic effect)
        effects["message"] = kwargs.get("message_text", "")

    elif spell == Spell.SCARE:
        # Target army −20 morale for 1 turn
        effects["morale_penalty"] = 20

    elif spell == Spell.SUMMON:
        # Summon a unit (handled by game engine based on race/class)
        effects["summon_unit_type"] = kwargs.get("unit_type", "monster")

    elif spell == Spell.TPORT:
        # Teleport army to target location
        effects["dest_x"] = target_x
        effects["dest_y"] = target_y

    elif spell == Spell.TRANSMUTE:
        # Convert resources (e.g. metals → jewels)
        conv_amt = int(kwargs.get("convert_amount", 0))
        effects["converted_metals"] = conv_amt
        effects["gained_jewels"] = conv_amt // 2

    elif spell == Spell.TRANSFER:
        # Transfer magic power to an allied nation
        xfer_amount = max(1, sdef.cost // 3)
        effects["power_transferred"] = xfer_amount

    return SpellResult(
        success=True,
        spell=spell,
        message=f"{sdef.name} cast successfully!",
        effects=effects,
    )


# ---------------------------------------------------------------------------
# Magic power regeneration
# ---------------------------------------------------------------------------

# Base regeneration per shrine (from magicX.c :: add_powers())
_BASE_REGEN_PER_SHRINE = 2
_WIZSKILL_DIVISOR = 20   # attr_wiz_skill / WIZSKILL_DIVISOR → regen bonus

# Theocrat class bonus
_THEOCRAT_REGEN_BONUS = 1.40   # +40%

# Player class constant
_PLAYER_CLASS_THEOCRAT = "THEOCRAT"


def regen_magic_power(
    current_military: int,
    current_civilian: int,
    current_wizardry: int,
    attr_wiz_skill: int,
    attr_spell_pts: int,
    race_traits: int,
    shrines_owned: int,
    player_class: str,
) -> tuple[int, int, int]:
    """
    Compute next-turn magic power levels (military, civilian, wizardry).

    Reference: magicX.c :: add_powers(), regen_powers()

    Each power type regenerates independently:
      base_regen = shrines * BASE_REGEN_PER_SHRINE + wiz_skill bonus
      Theocrat: shrines double power (each shrine counts twice).
      Race traits can modify specific power types.

    Powers are clamped to [0, attr_spell_pts] cap.
    """
    is_theocrat = player_class.upper() == _PLAYER_CLASS_THEOCRAT

    # Shrine contribution (Theocrat: doubled)
    shrine_count = shrines_owned * (2 if is_theocrat else 1)
    shrine_regen = shrine_count * _BASE_REGEN_PER_SHRINE

    # Skill bonus
    skill_bonus = attr_wiz_skill // _WIZSKILL_DIVISOR

    base_regen = shrine_regen + skill_bonus

    # Theocrat overall bonus
    if is_theocrat:
        base_regen = int(math.ceil(base_regen * _THEOCRAT_REGEN_BONUS))

    # Apply regeneration to each power type
    # Race traits (bitmask) can boost specific power types
    # RT_MAGICSKILL (from racesX.h) gives +1 to all regen
    _RT_MAGICSKILL = 0x0010
    magic_race_bonus = 1 if (race_traits & _RT_MAGICSKILL) else 0

    new_military = current_military + base_regen + magic_race_bonus
    new_civilian = current_civilian + base_regen + magic_race_bonus
    new_wizardry = current_wizardry + base_regen + magic_race_bonus

    # Cap at attr_spell_pts
    cap = max(0, attr_spell_pts)
    new_military = max(0, min(cap, new_military))
    new_civilian = max(0, min(cap, new_civilian))
    new_wizardry = max(0, min(cap, new_wizardry))

    return new_military, new_civilian, new_wizardry


# ---------------------------------------------------------------------------
# Terrain magic bonus (for combat resolution)
# ---------------------------------------------------------------------------

def mgk_sctval(altitude: int, vegetation: int, military_power: int) -> int:
    """
    Terrain combat bonus for magic-capable nations.

    Reference: magicX.c :: mgk_sctval()

    Certain terrains give higher magic combat bonuses to nations with military power.
    """
    # Higher ground = stronger magic emanation
    terrain_bonus = 0
    if altitude >= 8:      # mountain
        terrain_bonus = 3
    elif altitude >= 6:    # hill
        terrain_bonus = 2
    elif altitude >= 3:    # flat
        terrain_bonus = 1

    # Forest/jungle vegetation enhances nature-aligned military power
    if vegetation in (3, 4, 8):   # FOREST, JUNGLE, TAIGA
        terrain_bonus += 1

    return terrain_bonus if military_power > 0 else 0


# ---------------------------------------------------------------------------
# Passive magic power effects (applied each turn)
# ---------------------------------------------------------------------------

def apply_passive_powers(
    military_power: int,
    civilian_power: int,
    wizardry_power: int,
) -> dict:
    """
    Return dict of passive bonuses currently active based on power levels.

    These are applied by the turn processor to modify nation stats.
    Reference: computeX.c :: adjust_production(), combatA.c context checks.
    """
    bonuses: dict = {
        "combat_bonus": 0,
        "food_pct": 100,
        "wood_pct": 100,
        "metal_pct": 100,
        "jewel_pct": 100,
        "morale_regen": 0,
        "army_move_bonus": 0,
        "enemy_morale_penalty": 0,
    }

    # Military powers
    mil = MilitaryPower(military_power)
    if MilitaryPower.COMBAT_BON in mil:
        bonuses["combat_bonus"] += 10
    if MilitaryPower.TERROR in mil:
        bonuses["enemy_morale_penalty"] += 10
    if MilitaryPower.RALLY in mil:
        bonuses["morale_regen"] += 5

    # Civilian powers
    civ = CivilianPower(civilian_power)
    if CivilianPower.FARMING in civ:
        bonuses["food_pct"] += 20
    if CivilianPower.MINER in civ:
        bonuses["metal_pct"] += 20
        bonuses["jewel_pct"] += 20
    if CivilianPower.SWIFT in civ:
        bonuses["army_move_bonus"] += 1

    # Wizardry powers
    wiz = WizardryPower(wizardry_power)
    if WizardryPower.EARTH in wiz:
        bonuses["metal_pct"] += 10
    if WizardryPower.DRUIDISM in wiz:
        bonuses["wood_pct"] += 20

    return bonuses
