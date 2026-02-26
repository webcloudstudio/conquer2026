"""World (game instance) endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.world import World, world_admins
from app.routers.auth import get_current_user, require_world_admin
from app.schemas.world import AddCoAdminRequest, WorldAdminInfo, WorldCreate, WorldOut

router = APIRouter(prefix="/worlds", tags=["worlds"])


def _world_to_out(w: World) -> dict:
    """Serialize a World ORM instance to a dict matching WorldOut."""
    return {
        "id": w.id,
        "name": w.name,
        "mapx": w.mapx,
        "mapy": w.mapy,
        "turn": w.turn,
        "is_active": w.is_active,
        "is_maintenance": w.is_maintenance,
        "created_at": w.created_at,
        "admins": [{"user_id": u.id, "username": u.username} for u in w.admins],
    }


@router.get("/", response_model=list[WorldOut])
async def list_worlds(db: Annotated[AsyncSession, Depends(get_db)]) -> list[dict]:
    result = await db.execute(
        select(World)
        .where(World.is_active == True)  # noqa: E712
        .options(selectinload(World.admins))
    )
    return [_world_to_out(w) for w in result.scalars().all()]


@router.get("/mine", response_model=list[WorldOut])
async def list_my_worlds(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    """Worlds where the current user is an admin."""
    result = await db.execute(
        select(World)
        .join(world_admins, World.id == world_admins.c.world_id)
        .where(world_admins.c.user_id == current_user.id, World.is_active == True)  # noqa: E712
        .options(selectinload(World.admins))
    )
    return [_world_to_out(w) for w in result.scalars().all()]


@router.get("/{world_id}", response_model=WorldOut)
async def get_world(world_id: str, db: Annotated[AsyncSession, Depends(get_db)]) -> dict:
    result = await db.execute(
        select(World).where(World.id == world_id).options(selectinload(World.admins))
    )
    world = result.scalar_one_or_none()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    return _world_to_out(world)


@router.post("/", response_model=WorldOut, status_code=status.HTTP_201_CREATED)
async def create_world(
    body: WorldCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Any authenticated user can create a world and becomes its first admin."""
    world = World(name=body.name, mapx=body.mapx, mapy=body.mapy, creator_id=current_user.id)
    db.add(world)
    await db.flush()  # get world.id without committing
    await db.execute(
        insert(world_admins).values(world_id=world.id, user_id=current_user.id)
    )
    await db.commit()
    await db.refresh(world)
    # reload with admins
    result = await db.execute(
        select(World).where(World.id == world.id).options(selectinload(World.admins))
    )
    return _world_to_out(result.scalar_one())


@router.post("/{world_id}/admins", response_model=WorldAdminInfo, status_code=status.HTTP_201_CREATED)
async def add_co_admin(
    body: AddCoAdminRequest,
    world: Annotated[World, Depends(require_world_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """World admin adds another user as co-admin by username."""
    result = await db.execute(select(User).where(User.username == body.username))
    new_admin = result.scalar_one_or_none()
    if not new_admin:
        raise HTTPException(status_code=404, detail="User not found")
    # Idempotent: ignore if already an admin
    existing = await db.execute(
        select(world_admins).where(
            world_admins.c.world_id == world.id,
            world_admins.c.user_id == new_admin.id,
        )
    )
    if not existing.first():
        await db.execute(insert(world_admins).values(world_id=world.id, user_id=new_admin.id))
        await db.commit()
    return {"user_id": new_admin.id, "username": new_admin.username}
