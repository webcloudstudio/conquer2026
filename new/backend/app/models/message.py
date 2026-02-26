"""
Message model — in-game player-to-player messaging and news.

Replaces the original mail/news system from the C game.
Messages can be from nation to nation, or world-news broadcasts.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worlds.id"), nullable=False, index=True
    )

    # NULL sender = world news broadcast
    sender_nation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nations.id"), nullable=True
    )
    # NULL recipient = broadcast to all
    recipient_nation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nations.id"), nullable=True, index=True
    )

    subject: Mapped[str] = mapped_column(String(100), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    # Turn this message was sent on
    turn_sent: Mapped[int] = mapped_column(Integer, default=0)

    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    sender: Mapped["Nation | None"] = relationship(  # noqa: F821
        "Nation", foreign_keys=[sender_nation_id]
    )
    recipient: Mapped["Nation | None"] = relationship(  # noqa: F821
        "Nation", foreign_keys=[recipient_nation_id]
    )
