"""
Navy model — a naval fleet unit.

Derived from NAVY_STRUCT in gpl-release/Include/dataX.h
and ship-type constants in gpl-release/Include/navyX.h.

NSHP_NUMBER=4 ship types: warships, merchants, galleys, barges.
Each type has a count and an efficiency rating stored as separate columns.
"""

import uuid

from sqlalchemy import BigInteger, Boolean, ForeignKey, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Navy(Base):
    __tablename__ = "navies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nations.id"), nullable=False, index=True
    )

    # Ship counts by type
    warships: Mapped[int] = mapped_column(SmallInteger, default=0)
    merchants: Mapped[int] = mapped_column(SmallInteger, default=0)
    galleys: Mapped[int] = mapped_column(SmallInteger, default=0)
    barges: Mapped[int] = mapped_column(SmallInteger, default=0)

    # Efficiency per ship type (0-100)
    warship_eff: Mapped[int] = mapped_column(SmallInteger, default=100)
    merchant_eff: Mapped[int] = mapped_column(SmallInteger, default=100)
    galley_eff: Mapped[int] = mapped_column(SmallInteger, default=100)
    barge_eff: Mapped[int] = mapped_column(SmallInteger, default=100)

    # Position
    x: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    y: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    target_x: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    target_y: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    last_x: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    last_y: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    # State
    movement: Mapped[int] = mapped_column(SmallInteger, default=6)
    status: Mapped[int] = mapped_column(BigInteger, default=0)
    crew: Mapped[int] = mapped_column(SmallInteger, default=100)    # % of full crew
    people_per_hold: Mapped[int] = mapped_column(SmallInteger, default=0)
    supply: Mapped[int] = mapped_column(SmallInteger, default=10)

    # Cargo — units being transported
    carried_army_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("armies.id"), nullable=True
    )
    carried_caravan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("caravans.id"), nullable=True
    )

    # Cargo — materials
    cargo_talons: Mapped[int] = mapped_column(BigInteger, default=0)
    cargo_jewels: Mapped[int] = mapped_column(BigInteger, default=0)
    cargo_metals: Mapped[int] = mapped_column(BigInteger, default=0)
    cargo_food: Mapped[int] = mapped_column(BigInteger, default=0)
    cargo_wood: Mapped[int] = mapped_column(BigInteger, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    nation: Mapped["Nation"] = relationship("Nation", back_populates="navies")  # noqa: F821
    carried_army: Mapped["Army | None"] = relationship("Army", foreign_keys=[carried_army_id])  # noqa: F821
    carried_caravan: Mapped["Caravan | None"] = relationship(  # noqa: F821
        "Caravan", foreign_keys=[carried_caravan_id]
    )
