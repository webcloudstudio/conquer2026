"""Army endpoints — view armies, issue movement/attack/disband orders."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.army import Army
from app.models.command import Command, CommandStatus, CommandType
from app.models.nation import Nation
from app.models.user import User
from app.models.world import World
from app.routers.auth import get_current_user

router = APIRouter(prefix="/worlds/{world_id}/armies", tags=["armies"])


class ArmyOut(BaseModel):
    id: uuid.UUID
    nation_id: uuid.UUID
    unit_type: int
    strength: int
    supply: int
    efficiency: int
    movement: int
    x: int
    y: int
    is_active: bool

    model_config = {"from_attributes": True}


class MoveOrder(BaseModel):
    x: int
    y: int


class AttackOrder(BaseModel):
    x: int
    y: int


@router.get("/", response_model=list[ArmyOut])
async def list_armies(
    world_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[Army]:
    """List all active armies in the world (visible to all players for map rendering)."""
    nation_result = await db.execute(
        select(Nation.id).where(Nation.world_id == world_id, Nation.is_active == True)  # noqa: E712
    )
    nation_ids = [row[0] for row in nation_result.all()]
    if not nation_ids:
        return []

    result = await db.execute(
        select(Army).where(Army.nation_id.in_(nation_ids), Army.is_active == True)  # noqa: E712
    )
    return list(result.scalars().all())


@router.get("/mine", response_model=list[ArmyOut])
async def list_my_armies(
    world_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Army]:
    """List the current player's armies."""
    nation_result = await db.execute(
        select(Nation).where(Nation.world_id == world_id, Nation.user_id == current_user.id)
    )
    nation = nation_result.scalar_one_or_none()
    if not nation:
        raise HTTPException(status_code=403, detail="You have no nation in this world")

    result = await db.execute(
        select(Army).where(Army.nation_id == nation.id, Army.is_active == True)  # noqa: E712
    )
    return list(result.scalars().all())


async def _get_player_army(
    world_id: uuid.UUID,
    army_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> tuple[Army, Nation, World]:
    """Helper: fetch world, nation, and verify army ownership."""
    world_result = await db.execute(
        select(World).where(World.id == world_id, World.is_active == True)  # noqa: E712
    )
    world = world_result.scalar_one_or_none()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    nation_result = await db.execute(
        select(Nation).where(Nation.world_id == world_id, Nation.user_id == current_user.id)
    )
    nation = nation_result.scalar_one_or_none()
    if not nation:
        raise HTTPException(status_code=403, detail="You have no nation in this world")

    army_result = await db.execute(
        select(Army).where(
            Army.id == army_id,
            Army.nation_id == nation.id,
            Army.is_active == True,  # noqa: E712
        )
    )
    army = army_result.scalar_one_or_none()
    if not army:
        raise HTTPException(status_code=404, detail="Army not found or not yours")

    return army, nation, world


@router.post("/{army_id}/move")
async def order_move(
    world_id: uuid.UUID,
    army_id: uuid.UUID,
    body: MoveOrder,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Queue a move order for the army."""
    army, nation, world = await _get_player_army(world_id, army_id, current_user, db)

    cmd = Command(
        nation_id=nation.id,
        world_id=world_id,
        turn=world.turn,
        cmd_type=CommandType.ARMY_MOVE,
        status=CommandStatus.PENDING,
        target_id=str(army_id),
        x=body.x,
        y=body.y,
    )
    db.add(cmd)
    await db.commit()
    return {"queued": True, "army_id": str(army_id), "target": {"x": body.x, "y": body.y}}


@router.post("/{army_id}/attack")
async def order_attack(
    world_id: uuid.UUID,
    army_id: uuid.UUID,
    body: AttackOrder,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Queue an attack order against a target sector."""
    army, nation, world = await _get_player_army(world_id, army_id, current_user, db)

    cmd = Command(
        nation_id=nation.id,
        world_id=world_id,
        turn=world.turn,
        cmd_type=CommandType.ARMY_ATTACK,
        status=CommandStatus.PENDING,
        target_id=str(army_id),
        x=body.x,
        y=body.y,
    )
    db.add(cmd)
    await db.commit()
    return {"queued": True, "army_id": str(army_id), "target": {"x": body.x, "y": body.y}}


@router.post("/{army_id}/disband")
async def order_disband(
    world_id: uuid.UUID,
    army_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Queue a disband order for the army."""
    army, nation, world = await _get_player_army(world_id, army_id, current_user, db)

    cmd = Command(
        nation_id=nation.id,
        world_id=world_id,
        turn=world.turn,
        cmd_type=CommandType.ARMY_DISBAND,
        status=CommandStatus.PENDING,
        target_id=str(army_id),
    )
    db.add(cmd)
    await db.commit()
    return {"queued": True, "army_id": str(army_id)}
