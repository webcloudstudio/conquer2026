"""
World initialization service.

Creates sectors, NPC nations, and starting conditions from
the world_gen engine output. Mirrors conqrun -m (world creation).
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.world_gen import GeneratedWorld, generate_world
from app.models.army import Army
from app.models.nation import Nation, PlayerClass, Race
from app.models.sector import Designation, Sector
from app.models.world import World

# NPC nation definitions — mirror gpl-release/Src/nations
_NPC_RACES = [Race.LIZARD, Race.PIRATE, Race.SAVAGE, Race.NOMAD, Race.UNKNOWN]
_NPC_CLASSES = [
    PlayerClass.WARLORD,
    PlayerClass.TRADER,
    PlayerClass.MONSTER_LORD,
    PlayerClass.EMPIRE_BUILDER,
]
_NPC_NAMES = [
    "Lizardmen", "Pirates", "Savages", "Nomads", "Goblins",
    "Trolls", "Undead", "Bandits", "Mercenaries", "Cultists",
    "Raiders", "Barbarians",
]

# Starting resources for new nations
_START_RESOURCES = {
    "talons": 5000,
    "jewels": 100,
    "metals": 500,
    "food": 2000,
    "wood": 500,
}

# Starting army strength
_START_ARMY_SIZE = 2000


def _veg_to_designation(veg: int, altitude: int) -> int:
    """Pick an initial sector designation from terrain."""
    if altitude == 0:
        return Designation.UNDESIGNATED  # water — no designation
    if veg == 3:  # FOREST
        return Designation.FOREST
    if altitude >= 6:  # mountain/hill
        return Designation.UNDESIGNATED
    return Designation.UNDESIGNATED  # player will designate


async def initialize_world(
    world: World,
    db: AsyncSession,
    mapx: int = 79,
    mapy: int = 49,
    pwater: int = 35,
    pmount: int = 20,
    smoothings: int = 3,
    ptrade: int = 15,
    npc_count: int = 8,
    seed: int | None = None,
) -> GeneratedWorld:
    """
    Generate map + NPC nations and persist to DB.
    Called by admin endpoint when creating a new world.
    """
    gen = generate_world(mapx, mapy, pwater, pmount, smoothings, ptrade, seed)

    # Persist all sectors
    sector_map: dict[tuple[int, int], Sector] = {}
    for sdata in gen.sectors:
        sct = Sector(
            id=uuid.uuid4(),
            world_id=world.id,
            x=sdata.x,
            y=sdata.y,
            altitude=sdata.altitude,
            vegetation=sdata.vegetation,
            efficiency=sdata.efficiency,
            population=5000 if sdata.altitude > 0 else 0,
            minerals=sdata.minerals,
            tradegood=sdata.tradegood,
            designation=Designation.UNDESIGNATED,
        )
        db.add(sct)
        sector_map[(sdata.x, sdata.y)] = sct

    # Create NPC nations at spawn points
    npc_spawns = gen.npc_spawn_points[:npc_count]
    for i, (sx, sy) in enumerate(npc_spawns):
        race = _NPC_RACES[i % len(_NPC_RACES)]
        cls = _NPC_CLASSES[i % len(_NPC_CLASSES)]
        name = _NPC_NAMES[i % len(_NPC_NAMES)]

        npc = Nation(
            id=uuid.uuid4(),
            world_id=world.id,
            user_id=None,
            name=name[:10],
            race=race,
            player_class=cls,
            is_npc=True,
            capital_x=sx,
            capital_y=sy,
            center_x=sx,
            center_y=sy,
            mark=chr(ord("A") + i),
            **_START_RESOURCES,
        )
        db.add(npc)

        # Claim capital sector
        if (sx, sy) in sector_map:
            sct = sector_map[(sx, sy)]
            sct.owner_nation_id = npc.id
            sct.designation = Designation.CAPITAL
            sct.population = max(sct.population, 10000)

        # Claim a small ring of sectors
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = sx + dx, sy + dy
            if (nx, ny) in sector_map:
                ring_sct = sector_map[(nx, ny)]
                if ring_sct.owner_nation_id is None and ring_sct.altitude > 0:
                    ring_sct.owner_nation_id = npc.id
                    ring_sct.designation = Designation.FARM

        # Starting army
        army = Army(
            id=uuid.uuid4(),
            nation_id=npc.id,
            unit_type=0,
            strength=_START_ARMY_SIZE,
            x=sx,
            y=sy,
            efficiency=80,
            movement=4,
        )
        db.add(army)

    # Update world config
    world.mapx = mapx
    world.mapy = mapy

    await db.commit()
    return gen


async def initialize_player_nation(
    nation: Nation,
    spawn_x: int,
    spawn_y: int,
    db: AsyncSession,
) -> None:
    """
    Set up a newly joined player nation at their spawn location.
    Claims a small starting territory and creates a starting army.
    """
    from sqlalchemy import select

    world_id = nation.world_id

    # Claim spawn sector as capital
    result = await db.execute(
        select(Sector).where(
            Sector.world_id == world_id,
            Sector.x == spawn_x,
            Sector.y == spawn_y,
        )
    )
    capital = result.scalar_one_or_none()
    if capital:
        capital.owner_nation_id = nation.id
        capital.designation = Designation.CAPITAL
        capital.population = max(capital.population, 10000)

    nation.capital_x = spawn_x
    nation.capital_y = spawn_y
    nation.center_x = spawn_x
    nation.center_y = spawn_y

    # Apply starting resources
    for k, v in _START_RESOURCES.items():
        setattr(nation, k, v)

    # Starting army
    army = Army(
        id=uuid.uuid4(),
        nation_id=nation.id,
        unit_type=0,
        strength=_START_ARMY_SIZE,
        x=spawn_x,
        y=spawn_y,
        efficiency=100,
        movement=4,
    )
    db.add(army)
    await db.commit()
