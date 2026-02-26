"""
Caravan model — a trading unit.

Derived from CVN_STRUCT in gpl-release/Include/dataX.h.
"""

import uuid

from sqlalchemy import BigInteger, Boolean, ForeignKey, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Caravan(Base):
    __tablename__ = "caravans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nations.id"), nullable=False, index=True
    )

    efficiency: Mapped[int] = mapped_column(SmallInteger, default=100)

    # Position
    x: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    y: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    target_x: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    target_y: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    last_x: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    last_y: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    # State
    size: Mapped[int] = mapped_column(SmallInteger, default=1)    # number of wagons
    movement: Mapped[int] = mapped_column(SmallInteger, default=3)
    status: Mapped[int] = mapped_column(BigInteger, default=0)
    crew: Mapped[int] = mapped_column(SmallInteger, default=100)  # % of full crew
    people_per_wagon: Mapped[int] = mapped_column(SmallInteger, default=0)
    supply: Mapped[int] = mapped_column(SmallInteger, default=10)

    # Cargo
    cargo_talons: Mapped[int] = mapped_column(BigInteger, default=0)
    cargo_jewels: Mapped[int] = mapped_column(BigInteger, default=0)
    cargo_metals: Mapped[int] = mapped_column(BigInteger, default=0)
    cargo_food: Mapped[int] = mapped_column(BigInteger, default=0)
    cargo_wood: Mapped[int] = mapped_column(BigInteger, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    nation: Mapped["Nation"] = relationship("Nation", back_populates="caravans")  # noqa: F821
