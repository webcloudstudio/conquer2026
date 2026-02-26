"""Admin endpoints — turn processing, maintenance mode, world management, user management."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.world import World
from app.routers.auth import require_admin, require_world_admin
from app.services.turn_service import execute_turn

router = APIRouter(prefix="/admin", tags=["admin"])


class UserAdminOut(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("/worlds/{world_id}/process-turn")
async def process_turn(
    world: Annotated[World, Depends(require_world_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Manually trigger turn processing. Requires world admin."""
    if world.is_maintenance:
        raise HTTPException(status_code=423, detail="World is in maintenance mode")
    return await execute_turn(world, db)


@router.post("/worlds/{world_id}/maintenance")
async def toggle_maintenance(
    world: Annotated[World, Depends(require_world_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Toggle maintenance mode. Requires world admin. Mirrors conqrun -T."""
    world.is_maintenance = not world.is_maintenance
    await db.commit()
    return {"world_id": str(world.id), "maintenance": world.is_maintenance}


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

@router.get("/users", response_model=list[UserAdminOut])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> list[User]:
    """List all registered users."""
    result = await db.execute(select(User).order_by(User.created_at))
    return list(result.scalars().all())


@router.patch("/users/{user_id}/promote", response_model=UserAdminOut)
async def promote_user(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> User:
    """Grant admin privileges to a user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = True
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/users/{user_id}/demote", response_model=UserAdminOut)
async def demote_user(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
) -> User:
    """Revoke admin privileges from a user."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot demote yourself")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = False
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/users/{user_id}/deactivate", response_model=UserAdminOut)
async def deactivate_user(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
) -> User:
    """Deactivate (ban) a user account. They can no longer log in."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/users/{user_id}/activate", response_model=UserAdminOut)
async def activate_user(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> User:
    """Re-activate a previously deactivated user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    await db.commit()
    await db.refresh(user)
    return user
