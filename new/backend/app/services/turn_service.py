"""
Turn execution service — bridges ORM models and the pure-Python engine.

Loads world state from the database, runs process_turn(), and writes
results back. Also processes the pending command queue.

Reference execution order (executeX.c):
  1. Process commands (move orders, spell casts, etc.)
  2. Run sector production / consumption
  3. Run army movement / combat
  4. Run magic regeneration
  5. World events
  6. Victory point calculation
  7. Write news / messages
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.combat import Combatant, resolve_battle
from app.engine.turn_processor import (
    ArmyState,
    NationState,
    SectorState,
    process_turn,
)
from app.models.army import Army
from app.models.command import Command, CommandStatus, CommandType
from app.models.message import Message
from app.models.nation import Nation
from app.models.sector import Designation, Sector
from app.models.world import World

# ---------------------------------------------------------------------------
# State conversion helpers
# ---------------------------------------------------------------------------

def _nation_to_state(n: Nation) -> NationState:
    return NationState(
        id=str(n.id),
        attr_taxrate=n.attr_tax_rate,
        attr_eatrate=n.attr_eat_rate,
        attr_morale=n.attr_morale,
        attr_wiz_skill=n.attr_wiz_skill,
        attr_spell_pts=n.attr_spell_pts,
        res_talons=n.talons,
        res_jewels=n.jewels,
        res_metals=n.metals,
        res_food=n.food,
        res_wood=n.wood,
        power_military=n.power_fire,    # fire ≈ military
        power_civilian=n.power_water,   # water ≈ civilian
        power_wizardry=n.power_earth,   # earth ≈ wizardry
        race_traits=0,
        player_class=n.player_class.upper().replace("-", "_"),
        shrines_owned=0,  # computed below if needed
        victory_points=n.victory_points,
    )


def _state_to_nation(state: NationState, n: Nation) -> None:
    n.talons = max(0, state.res_talons)
    n.jewels = max(0, state.res_jewels)
    n.metals = max(0, state.res_metals)
    n.food = max(0, state.res_food)
    n.wood = max(0, state.res_wood)
    n.power_fire = state.power_military
    n.power_water = state.power_civilian
    n.power_earth = state.power_wizardry
    n.attr_morale = max(0, min(100, state.attr_morale))
    n.victory_points = state.victory_points


def _sector_to_state(s: Sector) -> SectorState:
    return SectorState(
        x=s.x,
        y=s.y,
        designation=s.designation,
        altitude=s.altitude,
        vegetation=s.vegetation,
        efficiency=s.efficiency,
        population=s.population,
        minerals=s.minerals,
        tradegood=s.tradegood,
        owner_nation_id=str(s.owner_nation_id) if s.owner_nation_id else None,
    )


def _army_to_state(a: Army) -> ArmyState:
    return ArmyState(
        id=str(a.id),
        nation_id=str(a.nation_id),
        unit_type=a.unit_type,
        strength=a.strength,
        supply=a.supply,
        morale=70,
        is_active=a.is_active,
    )


# ---------------------------------------------------------------------------
# Command processing
# ---------------------------------------------------------------------------

async def _process_commands(
    world: World,
    nations: dict[str, Nation],
    sector_map: dict[tuple[int, int], Sector],
    armies: dict[str, Army],
    db: AsyncSession,
    messages: list[str],
) -> None:
    """Process all pending commands for this turn."""
    result = await db.execute(
        select(Command).where(
            Command.world_id == world.id,
            Command.status == CommandStatus.PENDING,
        )
    )
    commands = result.scalars().all()

    for cmd in commands:
        nid = str(cmd.nation_id)
        nation = nations.get(nid)
        if nation is None:
            cmd.status = CommandStatus.FAILED
            cmd.result_msg = "Nation not found"
            continue

        try:
            if cmd.cmd_type == CommandType.DESIGNATE_SECTOR:
                await _cmd_designate(cmd, nation, sector_map, db)
            elif cmd.cmd_type == CommandType.ARMY_MOVE:
                await _cmd_army_move(cmd, armies, sector_map, db, messages)
            elif cmd.cmd_type == CommandType.ARMY_ATTACK:
                await _cmd_army_attack(cmd, nation, nations, armies, sector_map, db, messages)
            elif cmd.cmd_type == CommandType.ARMY_DISBAND:
                await _cmd_army_disband(cmd, armies, db)
            elif cmd.cmd_type == CommandType.DIPLOMACY:
                await _cmd_diplomacy(cmd, nation, nations, db)
            else:
                cmd.status = CommandStatus.DONE
                cmd.result_msg = f"Command {cmd.cmd_type} acknowledged"
        except Exception as e:  # noqa: BLE001
            cmd.status = CommandStatus.FAILED
            cmd.result_msg = str(e)[:200]


async def _cmd_designate(
    cmd: Command,
    nation: Nation,
    sector_map: dict[tuple[int, int], Sector],
    db: AsyncSession,
) -> None:
    sct = sector_map.get((cmd.x, cmd.y))
    if sct is None:
        cmd.status = CommandStatus.FAILED
        cmd.result_msg = "Sector not found"
        return
    if str(sct.owner_nation_id) != str(nation.id):
        cmd.status = CommandStatus.FAILED
        cmd.result_msg = "You do not own that sector"
        return
    new_desg = cmd.param_int or Designation.UNDESIGNATED
    sct.designation = new_desg
    cmd.status = CommandStatus.DONE
    cmd.result_msg = f"Sector ({cmd.x},{cmd.y}) designated to {new_desg}"


async def _cmd_army_move(
    cmd: Command,
    armies: dict[str, Army],
    sector_map: dict[tuple[int, int], Sector],
    db: AsyncSession,
    messages: list[str],
) -> None:
    if not cmd.target_id:
        cmd.status = CommandStatus.FAILED
        cmd.result_msg = "No army specified"
        return

    army = armies.get(cmd.target_id)
    if army is None or not army.is_active:
        cmd.status = CommandStatus.FAILED
        cmd.result_msg = "Army not found or inactive"
        return

    tx, ty = cmd.x, cmd.y
    if tx is None or ty is None:
        cmd.status = CommandStatus.FAILED
        cmd.result_msg = "No target coordinates"
        return

    from app.engine.world_gen import hex_distance
    dist = hex_distance(army.x, army.y, tx, ty)
    if dist > army.movement:
        cmd.status = CommandStatus.FAILED
        cmd.result_msg = f"Target too far: distance {dist} > movement {army.movement}"
        return

    army.last_x, army.last_y = army.x, army.y
    army.x, army.y = tx, ty
    cmd.status = CommandStatus.DONE
    cmd.result_msg = f"Army moved to ({tx},{ty})"
    messages.append(f"Army {army.id} moved from ({army.last_x},{army.last_y}) to ({tx},{ty})")


async def _cmd_army_attack(
    cmd: Command,
    attacker_nation: Nation,
    nations: dict[str, Nation],
    armies: dict[str, Army],
    sector_map: dict[tuple[int, int], Sector],
    db: AsyncSession,
    messages: list[str],
) -> None:
    if not cmd.target_id:
        cmd.status = CommandStatus.FAILED
        cmd.result_msg = "No attacking army specified"
        return

    atk_army = armies.get(cmd.target_id)
    if atk_army is None or not atk_army.is_active:
        cmd.status = CommandStatus.FAILED
        cmd.result_msg = "Attacking army not found"
        return

    tx, ty = cmd.x, cmd.y
    sct = sector_map.get((tx, ty))
    if sct is None:
        cmd.status = CommandStatus.FAILED
        cmd.result_msg = "Target sector not found"
        return

    # Find a defending army in that sector
    def_armies = [
        a for a in armies.values()
        if a.x == tx and a.y == ty and str(a.nation_id) != str(atk_army.nation_id)
        and a.is_active and a.strength > 0
    ]

    if def_armies:
        # Combat
        def_army = def_armies[0]
        atk = Combatant(
            strength=atk_army.strength,
            attack_bonus=attacker_nation.attack_bonus,
            defense_bonus=0,
            efficiency=atk_army.efficiency,
            unit_type=atk_army.unit_type,
        )
        def_nation = nations.get(str(def_army.nation_id))
        defn = Combatant(
            strength=def_army.strength,
            attack_bonus=0,
            defense_bonus=def_nation.defense_bonus if def_nation else 0,
            efficiency=def_army.efficiency,
            unit_type=def_army.unit_type,
            fortress_level=sct.efficiency // 10,
            is_fortified=sct.designation in (Designation.FORTRESS, Designation.CAPITAL),
        )
        result = resolve_battle(atk, defn, max_rounds=6)
        atk_army.strength = max(0, atk_army.strength - result.attacker_losses)
        def_army.strength = max(0, def_army.strength - result.defender_losses)
        if atk_army.strength == 0:
            atk_army.is_active = False
        if def_army.strength == 0:
            def_army.is_active = False

        msg = (
            f"Battle at ({tx},{ty}): attacker lost {result.attacker_losses}, "
            f"defender lost {result.defender_losses}. "
            f"{'Attacker wins!' if result.attacker_wins else 'Defender holds!'}"
        )
        messages.append(msg)

        # Capture if attacker wins and no defenders remain
        if result.attacker_wins and all(
            not a.is_active or a.strength == 0
            for a in def_armies
        ):
            old_owner = str(sct.owner_nation_id) if sct.owner_nation_id else None
            sct.owner_nation_id = atk_army.nation_id
            sct.efficiency = max(10, sct.efficiency // 3)
            atk_army.x, atk_army.y = tx, ty
            msg += f" Sector ({tx},{ty}) captured from nation {old_owner}!"
            messages.append(f"Sector ({tx},{ty}) captured!")

        cmd.result_msg = msg
    else:
        # No defenders — capture unopposed
        old_owner = str(sct.owner_nation_id) if sct.owner_nation_id else "nobody"
        sct.owner_nation_id = atk_army.nation_id
        sct.efficiency = max(20, sct.efficiency // 2)
        atk_army.x, atk_army.y = tx, ty
        cmd.result_msg = f"Sector ({tx},{ty}) seized from {old_owner} unopposed"
        messages.append(cmd.result_msg)

    cmd.status = CommandStatus.DONE


async def _cmd_army_disband(
    cmd: Command,
    armies: dict[str, Army],
    db: AsyncSession,
) -> None:
    if not cmd.target_id:
        cmd.status = CommandStatus.FAILED
        return
    army = armies.get(cmd.target_id)
    if army:
        army.is_active = False
        cmd.status = CommandStatus.DONE
        cmd.result_msg = "Army disbanded"
    else:
        cmd.status = CommandStatus.FAILED
        cmd.result_msg = "Army not found"


async def _cmd_diplomacy(
    cmd: Command,
    nation: Nation,
    nations: dict[str, Nation],
    db: AsyncSession,
) -> None:
    from app.models.nation import DiplomaticRelation, DiplomaticStatus
    if not cmd.target_id or not cmd.param_str:
        cmd.status = CommandStatus.FAILED
        cmd.result_msg = "Missing target or status"
        return

    try:
        new_status = DiplomaticStatus(cmd.param_str)
    except ValueError:
        cmd.status = CommandStatus.FAILED
        cmd.result_msg = f"Unknown diplomatic status: {cmd.param_str}"
        return

    result = await db.execute(
        select(DiplomaticRelation).where(
            DiplomaticRelation.nation_id == nation.id,
            DiplomaticRelation.target_nation_id == uuid.UUID(cmd.target_id),
        )
    )
    rel = result.scalar_one_or_none()
    if rel:
        rel.status = new_status
    else:
        rel = DiplomaticRelation(
            nation_id=nation.id,
            target_nation_id=uuid.UUID(cmd.target_id),
            status=new_status,
        )
        db.add(rel)

    cmd.status = CommandStatus.DONE
    cmd.result_msg = f"Diplomatic status set to {new_status}"


# ---------------------------------------------------------------------------
# Main turn execution
# ---------------------------------------------------------------------------

async def execute_turn(world: World, db: AsyncSession) -> dict:
    """
    Load world state, run the turn engine, write results back.
    Returns a summary dict.
    """
    # Load all nations
    result = await db.execute(
        select(Nation).where(Nation.world_id == world.id, Nation.is_active == True)  # noqa: E712
    )
    nation_list = result.scalars().all()

    # Load all sectors
    result = await db.execute(
        select(Sector).where(Sector.world_id == world.id)
    )
    sector_list = result.scalars().all()

    # Load all active armies
    result = await db.execute(
        select(Army).where(
            Army.nation_id.in_([n.id for n in nation_list]),
            Army.is_active == True,  # noqa: E712
        )
    )
    army_list = result.scalars().all()

    # Build lookup maps
    nations_orm: dict[str, Nation] = {str(n.id): n for n in nation_list}
    armies_orm: dict[str, Army] = {str(a.id): a for a in army_list}
    sector_map: dict[tuple[int, int], Sector] = {(s.x, s.y): s for s in sector_list}

    # Process command queue first
    cmd_messages: list[str] = []
    await _process_commands(world, nations_orm, sector_map, armies_orm, db, cmd_messages)

    # Convert to engine state objects
    nation_states: dict[str, NationState] = {
        nid: _nation_to_state(n) for nid, n in nations_orm.items()
    }
    sector_states = [_sector_to_state(s) for s in sector_list]

    # Count shrines per nation
    shrine_counts: dict[str, int] = {}
    for s in sector_list:
        if s.designation == Designation.SHRINE and s.owner_nation_id:
            nid = str(s.owner_nation_id)
            shrine_counts[nid] = shrine_counts.get(nid, 0) + 1
    for nid, ns in nation_states.items():
        ns.shrines_owned = shrine_counts.get(nid, 0)

    army_states = [_army_to_state(a) for a in army_list]

    # Run the engine
    log = process_turn(
        turn=world.turn,
        nations=nation_states,
        sectors=sector_states,
        armies=army_states,
    )

    # Write nation results back
    for nid, state in nation_states.items():
        n = nations_orm.get(nid)
        if n:
            _state_to_nation(state, n)

    # Write army results back (starvation deaths)
    for a_state in army_states:
        army = armies_orm.get(a_state.id)
        if army:
            army.strength = max(0, a_state.strength)
            if not a_state.is_active:
                army.is_active = False

    # Advance world turn counter
    world.turn += 1

    # Post world news message
    news = Message(
        id=uuid.uuid4(),
        world_id=world.id,
        sender_nation_id=None,
        recipient_nation_id=None,
        subject=f"Turn {world.turn} Results",
        body="\n".join(log.messages + cmd_messages),
        turn_sent=world.turn,
    )
    db.add(news)

    await db.commit()

    return {
        "world_id": str(world.id),
        "new_turn": world.turn,
        "nations_processed": len(nation_list),
        "sectors_processed": len(sector_list),
        "armies_starvations": len(log.army_starvation),
        "messages": log.messages[:10],
    }
