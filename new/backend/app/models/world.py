"""
World model — a single game instance.

Derived from the C struct s_world in gpl-release/Include/dataX.h.
The many char/short config fields are flattened into typed columns for
queryability; game-balance tweaks that are rarely queried live in JSON.
"""

import uuid
from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Integer, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class World(Base):
    __tablename__ = "worlds"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Map dimensions (0-based max coords, so actual size is mapx+1 × mapy+1)
    mapx: Mapped[int] = mapped_column(SmallInteger, default=79)
    mapy: Mapped[int] = mapped_column(SmallInteger, default=49)

    # Turn tracking
    turn: Mapped[int] = mapped_column(SmallInteger, default=0)
    start_turn: Mapped[int] = mapped_column(SmallInteger, default=0)

    # World state
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_maintenance: Mapped[bool] = mapped_column(Boolean, default=False)  # conqrun -T

    # God/admin account
    demigod_name: Mapped[str] = mapped_column(String(10), default="god")

    # World-aggregate stats (updated each turn)
    world_population: Mapped[int] = mapped_column(BigInteger, default=0)
    world_military: Mapped[int] = mapped_column(BigInteger, default=0)
    world_sectors: Mapped[int] = mapped_column(Integer, default=0)
    world_score: Mapped[int] = mapped_column(BigInteger, default=0)

    # World resource totals (updated each turn)
    w_talons: Mapped[int] = mapped_column(BigInteger, default=0)
    w_jewels: Mapped[int] = mapped_column(BigInteger, default=0)
    w_metals: Mapped[int] = mapped_column(BigInteger, default=0)
    w_food: Mapped[int] = mapped_column(BigInteger, default=0)
    w_wood: Mapped[int] = mapped_column(BigInteger, default=0)

    # NPC counts
    lizard_count: Mapped[int] = mapped_column(SmallInteger, default=3)
    savage_count: Mapped[int] = mapped_column(SmallInteger, default=3)
    nomad_count: Mapped[int] = mapped_column(SmallInteger, default=3)
    pirate_count: Mapped[int] = mapped_column(SmallInteger, default=2)

    # Mercenary pool
    merc_military: Mapped[int] = mapped_column(BigInteger, default=0)
    merc_attack_bonus: Mapped[int] = mapped_column(SmallInteger, default=0)
    merc_defense_bonus: Mapped[int] = mapped_column(SmallInteger, default=0)

    # Gameplay configuration (stored as JSON for flexibility)
    # Keys mirror the C world struct: pwater, pmount, num_dice, avg_damage, etc.
    config: Mapped[dict] = mapped_column(JSON, default=lambda: _default_config())

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    nations: Mapped[list["Nation"]] = relationship("Nation", back_populates="world")  # noqa: F821
    sectors: Mapped[list["Sector"]] = relationship("Sector", back_populates="world")  # noqa: F821
    cities: Mapped[list["City"]] = relationship("City", back_populates="world")  # noqa: F821
    artifacts: Mapped[list["Artifact"]] = relationship("Artifact", back_populates="world")  # noqa: F821
    events: Mapped[list["WorldEvent"]] = relationship("WorldEvent", back_populates="world")  # noqa: F821


def _default_config() -> dict:
    """Default world parameters matching the original C defaults."""
    return {
        # Terrain generation
        "pwater": 35,           # % water
        "pmount": 20,           # % mountains
        "smoothings": 3,        # map smoothing iterations
        "land_range": 2,        # displacement check for water
        "preject_land": 50,     # % chance rejection for land
        # NPC/event rates
        "pmonster": 5,          # % per year for monster reproduction
        "pmercmonst": 20,       # % of monsters who become mercs
        "ptrade": 15,           # % of sectors with trade goods
        "ptgmetal": 40,         # metal trade good percentage
        "ptgjewel": 40,         # jewel trade good percentage
        "ptgspell": 20,         # magic trade good percentage
        "numrandom": 2,         # random events per turn
        "numweather": 1,        # weather events per turn
        # Combat
        "num_dice": 2,
        "avg_damage": 50,
        "damage_limit": 30,
        "overmatch_adj": 10,
        "pmindamage": 10,
        "fleet_cbval": 10,
        "wagon_cbval": 5,
        # Economy
        "prevolt": 5,           # % yearly revolt level
        "pmercval": 30,         # % of disbanded troops who become mercs
        "pscout": 20,           # % chance to capture scouts
        "supplylimit": 10,
        "nvsplydist": 3,
        "cityxfdist": 5,
        # World setup
        "builddist": 5,         # min distance between starting nations
        "exposelvl": 10,
        "maxpts": 100,
        "maxdipadj": 50,
        "latestart": 3,
        "growthrate": 10,
        "bribelevel": 1000,
        # Flags
        "relative_map": False,
        "hexmap": True,
        "verify_login": True,
        "hide_scores": False,
        "hide_login": False,
        "demibuild": True,
        "demilimit": True,
    }
