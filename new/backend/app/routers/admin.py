"""Admin endpoints — turn processing, maintenance mode, world management."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.world import World
from app.routers.auth import require_admin
from app.services.turn_service import execute_turn
from app.services.world_service import initialize_world

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/worlds/{world_id}/process-turn")
async def process_turn(
    world_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> dict:
    """Manually trigger turn processing for a world."""
    result = await db.execute(select(World).where(World.id == world_id))
    world = result.scalar_one_or_none()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    if world.is_maintenance:
        raise HTTPException(status_code=423, detail="World is in maintenance mode")

    return await execute_turn(world, db)


@router.post("/worlds/{world_id}/initialize")
async def init_world(
    world_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
    mapx: int = 79,
    mapy: int = 49,
    pwater: int = 35,
    pmount: int = 20,
    npc_count: int = 8,
    seed: int | None = None,
) -> dict:
    """Generate map and NPC nations for a world. Mirrors conqrun -m."""
    result = await db.execute(select(World).where(World.id == world_id))
    world = result.scalar_one_or_none()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    gen = await initialize_world(
        world, db, mapx=mapx, mapy=mapy, pwater=pwater,
        pmount=pmount, npc_count=npc_count, seed=seed,
    )
    return {
        "world_id": str(world_id),
        "sectors": len(gen.sectors),
        "npc_nations": min(npc_count, len(gen.npc_spawn_points)),
        "mapx": mapx,
        "mapy": mapy,
    }


@router.post("/worlds/{world_id}/maintenance")
async def toggle_maintenance(
    world_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> dict:
    """Toggle maintenance mode (blocks player logins). Mirrors conqrun -T."""
    result = await db.execute(select(World).where(World.id == world_id))
    world = result.scalar_one_or_none()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    world.is_maintenance = not world.is_maintenance
    await db.commit()
    return {"world_id": str(world_id), "maintenance": world.is_maintenance}
