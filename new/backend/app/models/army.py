"""
Army model — a land military unit.

Derived from ARMY_STRUCT in gpl-release/Include/dataX.h
and unit-type definitions in gpl-release/Include/armyX.h.
"""

import uuid

from sqlalchemy import BigInteger, Boolean, ForeignKey, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Army(Base):
    __tablename__ = "armies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nations.id"), nullable=False, index=True
    )

    # Unit type index into the army type table (0–38+ in original)
    unit_type: Mapped[int] = mapped_column(SmallInteger, default=38)  # DEFAULT_ARMYTYPE=38

    # Efficiency (0-100); max_efficiency is the ceiling the unit can recover to
    max_efficiency: Mapped[int] = mapped_column(SmallInteger, default=100)
    efficiency: Mapped[int] = mapped_column(SmallInteger, default=100)

    # Position
    x: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    y: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    target_x: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    target_y: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    last_x: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    last_y: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    # Combat
    strength: Mapped[int] = mapped_column(BigInteger, default=1000)  # number of soldiers
    movement: Mapped[int] = mapped_column(SmallInteger, default=4)   # movement points per turn
    status: Mapped[int] = mapped_column(BigInteger, default=0)       # bitmask flags

    # Magic / leadership
    spell_points: Mapped[int] = mapped_column(SmallInteger, default=0)
    supply: Mapped[int] = mapped_column(SmallInteger, default=10)    # food supply per man

    # Leader linkage (NULL for regular units, set for armies led by a leader unit)
    leader_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("armies.id"), nullable=True
    )

    # Soft-delete rather than hard-delete so history is preserved
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    nation: Mapped["Nation"] = relationship("Nation", back_populates="armies")  # noqa: F821
    leader: Mapped["Army | None"] = relationship("Army", remote_side="Army.id")
