"""
Sector model — a single hex on the world map.

Derived from SCT_STRUCT in gpl-release/Include/dataX.h.
Sectors are addressed by (world_id, x, y).
"""

import enum
import uuid

from sqlalchemy import BigInteger, ForeignKey, SmallInteger, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Designation(int, enum.Enum):
    """Major sector designations — mirrors the MAJ_NUMBER=16 desig types in the C code."""
    UNDESIGNATED = 0
    FARM = 1
    MINE = 2
    CITY = 3
    FORTRESS = 4
    SHRINE = 5
    FOREST = 6
    WASTELAND = 7
    ROAD = 8
    PORT = 9
    CAPITAL = 10
    RUINS = 11
    PASTURE = 12
    ORCHARD = 13
    QUARRY = 14
    TRADE_POST = 15


class Vegetation(int, enum.Enum):
    NONE = 0
    SPARSE = 1
    GRASSLAND = 2
    FOREST = 3
    JUNGLE = 4
    SWAMP = 5
    DESERT = 6
    TUNDRA = 7
    TAIGA = 8
    WETLAND = 9
    MEADOW = 10
    SCRUB = 11


class Sector(Base):
    __tablename__ = "sectors"
    __table_args__ = (
        UniqueConstraint("world_id", "x", "y", name="uq_sector_world_xy"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worlds.id"), nullable=False, index=True
    )
    owner_nation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nations.id"), nullable=True, index=True
    )

    x: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    y: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    designation: Mapped[int] = mapped_column(SmallInteger, default=Designation.UNDESIGNATED)
    altitude: Mapped[int] = mapped_column(SmallInteger, default=0)    # 0=water, higher=mountain
    vegetation: Mapped[int] = mapped_column(SmallInteger, default=Vegetation.NONE)
    efficiency: Mapped[int] = mapped_column(SmallInteger, default=0)  # 0-100
    population: Mapped[int] = mapped_column(BigInteger, default=0)
    minerals: Mapped[int] = mapped_column(SmallInteger, default=0)    # jewel/metal value
    tradegood: Mapped[int] = mapped_column(SmallInteger, default=0)   # exotic goods

    # Relationships
    world: Mapped["World"] = relationship("World", back_populates="sectors")  # noqa: F821
    owner: Mapped["Nation | None"] = relationship("Nation")  # noqa: F821
