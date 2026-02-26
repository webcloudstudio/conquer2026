"""Nation endpoints — join a game, view nation state."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.nation import Nation
from app.models.user import User
from app.models.world import World
from app.routers.auth import get_current_user
from app.schemas.nation import NationCreate, NationOut

router = APIRouter(prefix="/worlds/{world_id}/nations", tags=["nations"])


@router.get("/", response_model=list[NationOut])
async def list_nations(
    world_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]
) -> list[Nation]:
    result = await db.execute(
        select(Nation).where(Nation.world_id == world_id, Nation.is_active == True)  # noqa: E712
    )
    return list(result.scalars().all())


@router.get("/{nation_id}", response_model=NationOut)
async def get_nation(
    world_id: uuid.UUID,
    nation_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Nation:
    result = await db.execute(
        select(Nation).where(Nation.id == nation_id, Nation.world_id == world_id)
    )
    nation = result.scalar_one_or_none()
    if not nation:
        raise HTTPException(status_code=404, detail="Nation not found")
    return nation


@router.post("/", response_model=NationOut, status_code=status.HTTP_201_CREATED)
async def join_world(
    world_id: uuid.UUID,
    body: NationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Nation:
    """Register the current user as a new nation in this world."""
    # Verify world exists and is active
    world_result = await db.execute(
        select(World).where(World.id == world_id, World.is_active == True)  # noqa: E712
    )
    world = world_result.scalar_one_or_none()
    if not world:
        raise HTTPException(status_code=404, detail="World not found or not active")

    # One nation per user per world
    existing = await db.execute(
        select(Nation).where(Nation.world_id == world_id, Nation.user_id == current_user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You already have a nation in this world")

    # Name uniqueness within world
    name_check = await db.execute(
        select(Nation).where(Nation.world_id == world_id, Nation.name == body.name)
    )
    if name_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Nation name already taken in this world")

    nation = Nation(
        world_id=world_id,
        user_id=current_user.id,
        name=body.name,
        leader_title=body.leader_title,
        race=body.race,
        player_class=body.player_class,
    )
    db.add(nation)
    await db.commit()
    await db.refresh(nation)
    return nation
