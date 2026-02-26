"""
Command model — player order queue processed at turn execution.

Players issue commands during the inter-turn window. On turn execution
each command is resolved in order. Mirrors the .exc command file system
from the original C game (iodataX.c command queue).
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CommandType(str, enum.Enum):
    # Army commands
    ARMY_MOVE = "army_move"
    ARMY_ATTACK = "army_attack"
    ARMY_DEFEND = "army_defend"
    ARMY_DESIGNATE = "army_designate"
    ARMY_DISBAND = "army_disband"
    ARMY_CAST = "army_cast"
    # Nation commands
    DESIGNATE_SECTOR = "designate_sector"
    SET_TRADE = "set_trade"
    DIPLOMACY = "diplomacy"
    # Navy commands
    NAVY_MOVE = "navy_move"
    NAVY_PATROL = "navy_patrol"
    # Caravan commands
    CARAVAN_ROUTE = "caravan_route"
    CARAVAN_DELIVER = "caravan_deliver"


class CommandStatus(str, enum.Enum):
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Command(Base):
    __tablename__ = "commands"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nations.id"), nullable=False, index=True
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worlds.id"), nullable=False, index=True
    )

    # Which turn this command was submitted for
    turn: Mapped[int] = mapped_column(Integer, default=0)

    cmd_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=CommandStatus.PENDING)

    # Target entity (army id, navy id, etc.) — stored as string UUID
    target_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Map coordinates for move/attack/designate
    x: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    y: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    # Integer parameter (designation type, spell id, diplomatic status, etc.)
    param_int: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # String parameter (message text, etc.)
    param_str: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Result message after processing
    result_msg: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    nation: Mapped["Nation"] = relationship("Nation")  # noqa: F821
