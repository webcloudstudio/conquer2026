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

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/worlds/{world_id}/process-turn")
async def process_turn(
    world_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> dict:
    """Manually trigger turn processing for a world. (Phase 2: engine not yet implemented.)"""
    result = await db.execute(select(World).where(World.id == world_id))
    world = result.scalar_one_or_none()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    # TODO Phase 2: call engine.turn_processor.process_turn(world, db)
    world.turn += 1
    await db.commit()
    return {"world_id": str(world_id), "new_turn": world.turn, "status": "processed"}


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
