"""World (game instance) endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.world import World
from app.routers.auth import require_admin
from app.schemas.world import WorldCreate, WorldOut

router = APIRouter(prefix="/worlds", tags=["worlds"])


@router.get("/", response_model=list[WorldOut])
async def list_worlds(db: Annotated[AsyncSession, Depends(get_db)]) -> list[World]:
    result = await db.execute(select(World).where(World.is_active == True))  # noqa: E712
    return list(result.scalars().all())


@router.get("/{world_id}", response_model=WorldOut)
async def get_world(world_id: str, db: Annotated[AsyncSession, Depends(get_db)]) -> World:
    result = await db.execute(select(World).where(World.id == world_id))
    world = result.scalar_one_or_none()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    return world


@router.post("/", response_model=WorldOut, status_code=status.HTTP_201_CREATED)
async def create_world(
    body: WorldCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> World:
    world = World(name=body.name, mapx=body.mapx, mapy=body.mapy)
    db.add(world)
    await db.commit()
    await db.refresh(world)
    return world
