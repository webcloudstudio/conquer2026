"""Sector (map tile) endpoints — read map state, designate sectors."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.command import Command, CommandStatus, CommandType
from app.models.nation import Nation
from app.models.sector import Sector
from app.models.user import User
from app.models.world import World
from app.routers.auth import get_current_user

router = APIRouter(prefix="/worlds/{world_id}/sectors", tags=["sectors"])


class SectorOut(BaseModel):
    x: int
    y: int
    altitude: int
    vegetation: int
    designation: int
    efficiency: int
    population: int
    minerals: int
    tradegood: int
    owner_nation_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class DesignateRequest(BaseModel):
    designation: int


@router.get("/", response_model=list[SectorOut])
async def list_sectors(
    world_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[Sector]:
    """Return all sectors for the map. Used to render the hex grid."""
    result = await db.execute(select(Sector).where(Sector.world_id == world_id))
    return list(result.scalars().all())


@router.get("/{x}/{y}", response_model=SectorOut)
async def get_sector(
    world_id: uuid.UUID,
    x: int,
    y: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Sector:
    result = await db.execute(
        select(Sector).where(Sector.world_id == world_id, Sector.x == x, Sector.y == y)
    )
    sct = result.scalar_one_or_none()
    if not sct:
        raise HTTPException(status_code=404, detail="Sector not found")
    return sct


@router.post("/{x}/{y}/designate")
async def designate_sector(
    world_id: uuid.UUID,
    x: int,
    y: int,
    body: DesignateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Queue a designation command for the player's owned sector."""
    # Validate world
    world_result = await db.execute(
        select(World).where(World.id == world_id, World.is_active == True)  # noqa: E712
    )
    world = world_result.scalar_one_or_none()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    # Get player's nation
    nation_result = await db.execute(
        select(Nation).where(Nation.world_id == world_id, Nation.user_id == current_user.id)
    )
    nation = nation_result.scalar_one_or_none()
    if not nation:
        raise HTTPException(status_code=403, detail="You have no nation in this world")

    # Verify ownership
    sector_result = await db.execute(
        select(Sector).where(Sector.world_id == world_id, Sector.x == x, Sector.y == y)
    )
    sct = sector_result.scalar_one_or_none()
    if not sct:
        raise HTTPException(status_code=404, detail="Sector not found")
    if str(sct.owner_nation_id) != str(nation.id):
        raise HTTPException(status_code=403, detail="You do not own that sector")

    # Queue command for next turn
    cmd = Command(
        nation_id=nation.id,
        world_id=world_id,
        turn=world.turn,
        cmd_type=CommandType.DESIGNATE_SECTOR,
        status=CommandStatus.PENDING,
        x=x,
        y=y,
        param_int=body.designation,
    )
    db.add(cmd)
    await db.commit()
    return {"queued": True, "x": x, "y": y, "designation": body.designation}
