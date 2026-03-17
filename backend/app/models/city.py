"""
City model — a named settlement on the map.

Derived from CITY_STRUCT in gpl-release/Include/dataX.h.
Cities are separate from sector designations — a sector can have a city
structure that carries inventory, distribution rules, and fortification data.
"""

import uuid

from sqlalchemy import JSON, BigInteger, Boolean, ForeignKey, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class City(Base):
    __tablename__ = "cities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worlds.id"), nullable=False, index=True
    )
    nation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nations.id"), nullable=True, index=True
    )

    x: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    y: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(10), nullable=False)

    initial_population: Mapped[int] = mapped_column(SmallInteger, default=0)
    efficiency: Mapped[int] = mapped_column(SmallInteger, default=50)
    weight: Mapped[int] = mapped_column(SmallInteger, default=10)   # distribution weighting
    fortress: Mapped[int] = mapped_column(SmallInteger, default=0)  # fortification value

    # Current material stockpile in the city
    talons: Mapped[int] = mapped_column(BigInteger, default=0)
    jewels: Mapped[int] = mapped_column(BigInteger, default=0)
    metals: Mapped[int] = mapped_column(BigInteger, default=0)
    food: Mapped[int] = mapped_column(BigInteger, default=0)
    wood: Mapped[int] = mapped_column(BigInteger, default=0)

    # Initial distribution amounts (used when distributing from city to sectors)
    init_talons: Mapped[int] = mapped_column(BigInteger, default=0)
    init_jewels: Mapped[int] = mapped_column(BigInteger, default=0)
    init_metals: Mapped[int] = mapped_column(BigInteger, default=0)
    init_food: Mapped[int] = mapped_column(BigInteger, default=0)
    init_wood: Mapped[int] = mapped_column(BigInteger, default=0)

    # Starting talons
    start_talons: Mapped[int] = mapped_column(BigInteger, default=0)

    # Minimum amounts to keep in city (don't distribute below these levels)
    min_talons: Mapped[int] = mapped_column(BigInteger, default=0)
    min_jewels: Mapped[int] = mapped_column(BigInteger, default=0)
    min_metals: Mapped[int] = mapped_column(BigInteger, default=0)
    min_food: Mapped[int] = mapped_column(BigInteger, default=0)
    min_wood: Mapped[int] = mapped_column(BigInteger, default=0)

    # Auto-distribution flags (JSON: list of 5 ints, one per material)
    auto_flags: Mapped[list] = mapped_column(JSON, default=lambda: [0, 0, 0, 0, 0])

    # Navy/caravan command flag (bitmask)
    cmd_flag: Mapped[int] = mapped_column(BigInteger, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    world: Mapped["World"] = relationship("World", back_populates="cities")  # noqa: F821
    nation: Mapped["Nation | None"] = relationship("Nation", back_populates="cities")  # noqa: F821
