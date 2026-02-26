"""
Magic engine — translates magicA.c / magicX.c logic to Python.

Reference: gpl-release/Src/magicA.c, gpl-release/Src/magicX.c,
           gpl-release/Include/spellsX.h

Spells (10 total, from spellsX.h):
  COMBAT, FLIGHT, HEAL, QUAKE, SENDING, SCARE, SUMMON, TPORT, TRANSMUTE, TRANSFER

Powers (MAG_NUMBER=3): fire, water, earth

Phase 1: stubs with type signatures.
Phase 2: full implementation.
"""

from enum import IntEnum


class Spell(IntEnum):
    COMBAT = 0
    FLIGHT = 1
    HEAL = 2
    QUAKE = 3
    SENDING = 4
    SCARE = 5
    SUMMON = 6
    TPORT = 7
    TRANSMUTE = 8
    TRANSFER = 9


class MagicPower(IntEnum):
    FIRE = 0
    WATER = 1
    EARTH = 2


# Spell costs match spellsX.h values (Phase 2: import from data file)
SPELL_COSTS = {
    Spell.COMBAT: 10,
    Spell.FLIGHT: 8,
    Spell.HEAL: 12,
    Spell.QUAKE: 20,
    Spell.SENDING: 5,
    Spell.SCARE: 6,
    Spell.SUMMON: 25,
    Spell.TPORT: 15,
    Spell.TRANSMUTE: 18,
    Spell.TRANSFER: 10,
}


def can_cast(
    spell: Spell,
    caster_spell_points: int,
    power_fire: int,
    power_water: int,
    power_earth: int,
    is_full_caster: bool = False,
) -> bool:
    """
    Check whether a unit can cast a given spell.
    Full casters can cast any spell; partial casters are limited.

    Reference: magicX.c :: can_cast_spell()
    """
    raise NotImplementedError("Phase 2")


def cast_spell(
    spell: Spell,
    caster_spell_points: int,
    target_x: int,
    target_y: int,
    **kwargs: object,
) -> dict:
    """
    Execute a spell and return a result dict describing what happened.

    Reference: magicA.c :: cast_spell()
    """
    raise NotImplementedError("Phase 2")


def regen_magic_power(
    current_fire: int,
    current_water: int,
    current_earth: int,
    attr_wiz_skill: int,
    attr_spell_pts: int,
    race_traits: int,
    shrines_owned: int,
    player_class: str,
) -> tuple[int, int, int]:
    """
    Compute next-turn magic power levels.

    Theocrat class: +40% regen, shrines double power.

    Reference: magicA.c :: regen_powers()
    """
    raise NotImplementedError("Phase 2")
