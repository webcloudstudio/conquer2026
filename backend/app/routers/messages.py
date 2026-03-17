"""Messaging endpoints — in-game nation-to-nation mail and world news."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.message import Message
from app.models.nation import Nation
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter(prefix="/worlds/{world_id}/messages", tags=["messages"])


class MessageOut(BaseModel):
    id: uuid.UUID
    sender_nation_id: uuid.UUID | None
    recipient_nation_id: uuid.UUID | None
    subject: str
    body: str
    is_read: bool
    turn_sent: int

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    recipient_nation_id: uuid.UUID
    subject: str
    body: str


@router.get("/", response_model=list[MessageOut])
async def get_inbox(
    world_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Message]:
    """Fetch all messages for the player's nation (direct + world broadcasts)."""
    nation_result = await db.execute(
        select(Nation).where(Nation.world_id == world_id, Nation.user_id == current_user.id)
    )
    nation = nation_result.scalar_one_or_none()
    if not nation:
        raise HTTPException(status_code=403, detail="You have no nation in this world")

    result = await db.execute(
        select(Message).where(
            Message.world_id == world_id,
            or_(
                Message.recipient_nation_id == nation.id,
                Message.recipient_nation_id.is_(None),  # world broadcasts
            ),
        ).order_by(Message.turn_sent.desc())
    )
    return list(result.scalars().all())


@router.post("/send", response_model=MessageOut)
async def send_message(
    world_id: uuid.UUID,
    body: SendMessageRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Message:
    """Send a message to another nation."""
    nation_result = await db.execute(
        select(Nation).where(Nation.world_id == world_id, Nation.user_id == current_user.id)
    )
    nation = nation_result.scalar_one_or_none()
    if not nation:
        raise HTTPException(status_code=403, detail="You have no nation in this world")

    # Verify recipient exists
    recip_result = await db.execute(
        select(Nation).where(
            Nation.id == body.recipient_nation_id,
            Nation.world_id == world_id,
        )
    )
    if not recip_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Recipient nation not found")

    from app.models.world import World
    world_result = await db.execute(select(World).where(World.id == world_id))
    world = world_result.scalar_one_or_none()
    current_turn = world.turn if world else 0

    msg = Message(
        id=uuid.uuid4(),
        world_id=world_id,
        sender_nation_id=nation.id,
        recipient_nation_id=body.recipient_nation_id,
        subject=body.subject[:100],
        body=body.body,
        turn_sent=current_turn,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


@router.post("/{message_id}/read")
async def mark_read(
    world_id: uuid.UUID,
    message_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Mark a message as read."""
    nation_result = await db.execute(
        select(Nation).where(Nation.world_id == world_id, Nation.user_id == current_user.id)
    )
    nation = nation_result.scalar_one_or_none()
    if not nation:
        raise HTTPException(status_code=403, detail="You have no nation in this world")

    msg_result = await db.execute(
        select(Message).where(
            Message.id == message_id,
            Message.recipient_nation_id == nation.id,
        )
    )
    msg = msg_result.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    msg.is_read = True
    await db.commit()
    return {"ok": True}
