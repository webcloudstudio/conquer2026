"""
Nation model — the central game entity for a player or NPC.

Derived from NTN_STRUCT in gpl-release/Include/dataX.h.
The 19 national attributes (butesX.h) are stored as individual columns
for query efficiency. Resources (5 material types) are named columns.
Magic powers (3 types) are named columns.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Race(str, enum.Enum):
    HUMAN = "human"
    ELF = "elf"
    DWARF = "dwarf"
    ORC = "orc"
    HALFLING = "halfling"
    LIZARD = "lizard"      # NPC
    PIRATE = "pirate"      # NPC
    SAVAGE = "savage"      # NPC
    NOMAD = "nomad"        # NPC
    UNKNOWN = "unknown"    # NPC


class PlayerClass(str, enum.Enum):
    EMPIRE_BUILDER = "empire_builder"
    WARLORD = "warlord"
    TRADER = "trader"
    THEOCRAT = "theocrat"
    DIPLOMAT = "diplomat"
    ARTIFACT_HUNTER = "artifact_hunter"
    PATHFINDER = "pathfinder"
    MONSTER_LORD = "monster_lord"


class DiplomaticStatus(str, enum.Enum):
    ALLIED = "allied"
    NEUTRAL = "neutral"
    HOSTILE = "hostile"
    WAR = "war"
    CONFEDERATE = "confederate"
    JIHAD = "jihad"


class Nation(Base):
    __tablename__ = "nations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worlds.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )

    # Identity
    name: Mapped[str] = mapped_column(String(10), nullable=False)
    leader_title: Mapped[str] = mapped_column(String(10), default="Leader")
    race: Mapped[str] = mapped_column(String(20), default=Race.HUMAN)
    player_class: Mapped[str] = mapped_column(String(30), default=PlayerClass.EMPIRE_BUILDER)
    mark: Mapped[str] = mapped_column(String(1), default="?")  # unique symbol on map

    # Position
    capital_x: Mapped[int] = mapped_column(SmallInteger, default=0)
    capital_y: Mapped[int] = mapped_column(SmallInteger, default=0)
    center_x: Mapped[int] = mapped_column(SmallInteger, default=0)
    center_y: Mapped[int] = mapped_column(SmallInteger, default=0)

    # Combat modifiers
    attack_bonus: Mapped[int] = mapped_column(SmallInteger, default=0)
    defense_bonus: Mapped[int] = mapped_column(SmallInteger, default=0)
    max_movement: Mapped[int] = mapped_column(SmallInteger, default=4)
    reproduction_rate: Mapped[int] = mapped_column(SmallInteger, default=10)

    # Status
    is_npc: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    score: Mapped[int] = mapped_column(BigInteger, default=0)
    victory_points: Mapped[int] = mapped_column(BigInteger, default=0)

    # Population & military totals (updated each turn)
    total_civilians: Mapped[int] = mapped_column(BigInteger, default=0)
    total_military: Mapped[int] = mapped_column(BigInteger, default=0)
    total_monsters: Mapped[int] = mapped_column(BigInteger, default=0)
    total_leaders: Mapped[int] = mapped_column(BigInteger, default=0)
    total_sectors: Mapped[int] = mapped_column(Integer, default=0)
    total_ships: Mapped[int] = mapped_column(SmallInteger, default=0)
    total_wagons: Mapped[int] = mapped_column(SmallInteger, default=0)

    # Resources (current stockpile)
    talons: Mapped[int] = mapped_column(BigInteger, default=0)   # money/currency
    jewels: Mapped[int] = mapped_column(BigInteger, default=0)
    metals: Mapped[int] = mapped_column(BigInteger, default=0)
    food: Mapped[int] = mapped_column(BigInteger, default=0)
    wood: Mapped[int] = mapped_column(BigInteger, default=0)

    # Resources produced this turn
    talons_produced: Mapped[int] = mapped_column(BigInteger, default=0)
    jewels_produced: Mapped[int] = mapped_column(BigInteger, default=0)
    metals_produced: Mapped[int] = mapped_column(BigInteger, default=0)
    food_produced: Mapped[int] = mapped_column(BigInteger, default=0)
    wood_produced: Mapped[int] = mapped_column(BigInteger, default=0)

    # Magic powers (MAG_NUMBER=3: fire/earth/water or equivalent)
    power_fire: Mapped[int] = mapped_column(BigInteger, default=0)
    power_water: Mapped[int] = mapped_column(BigInteger, default=0)
    power_earth: Mapped[int] = mapped_column(BigInteger, default=0)

    # National attributes (BUTE_NUMBER=19, from butesX.h)
    attr_charity: Mapped[int] = mapped_column(SmallInteger, default=50)
    attr_comm_range: Mapped[int] = mapped_column(SmallInteger, default=30)
    attr_currency: Mapped[int] = mapped_column(SmallInteger, default=50)
    attr_eat_rate: Mapped[int] = mapped_column(SmallInteger, default=10)   # /10 = 1.0 food/person
    attr_health: Mapped[int] = mapped_column(SmallInteger, default=50)
    attr_inflation: Mapped[int] = mapped_column(SmallInteger, default=0)
    attr_jewelwork: Mapped[int] = mapped_column(SmallInteger, default=50)
    attr_knowledge: Mapped[int] = mapped_column(SmallInteger, default=50)
    attr_merc_rep: Mapped[int] = mapped_column(SmallInteger, default=50)
    attr_metalwork: Mapped[int] = mapped_column(SmallInteger, default=50)
    attr_mining: Mapped[int] = mapped_column(SmallInteger, default=50)
    attr_morale: Mapped[int] = mapped_column(SmallInteger, default=70)
    attr_popularity: Mapped[int] = mapped_column(SmallInteger, default=50)
    attr_reputation: Mapped[int] = mapped_column(SmallInteger, default=50)
    attr_spell_pts: Mapped[int] = mapped_column(SmallInteger, default=0)
    attr_spoil_rate: Mapped[int] = mapped_column(SmallInteger, default=10)
    attr_tax_rate: Mapped[int] = mapped_column(SmallInteger, default=30)
    attr_terror: Mapped[int] = mapped_column(SmallInteger, default=0)
    attr_wiz_skill: Mapped[int] = mapped_column(SmallInteger, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    world: Mapped["World"] = relationship("World", back_populates="nations")  # noqa: F821
    user: Mapped["User | None"] = relationship("User", back_populates="nations")  # noqa: F821
    armies: Mapped[list["Army"]] = relationship("Army", back_populates="nation")  # noqa: F821
    navies: Mapped[list["Navy"]] = relationship("Navy", back_populates="nation")  # noqa: F821
    caravans: Mapped[list["Caravan"]] = relationship("Caravan", back_populates="nation")  # noqa: F821
    cities: Mapped[list["City"]] = relationship("City", back_populates="nation")  # noqa: F821
    held_artifacts: Mapped[list["Artifact"]] = relationship(  # noqa: F821
        "Artifact", back_populates="holder_nation"
    )
    diplomatic_stances: Mapped[list["DiplomaticRelation"]] = relationship(  # noqa: F821
        "DiplomaticRelation",
        foreign_keys="DiplomaticRelation.nation_id",
        back_populates="nation",
    )


class DiplomaticRelation(Base):
    """Bilateral diplomatic status between two nations. Row per (nation, target) pair."""

    __tablename__ = "diplomatic_relations"

    nation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nations.id"), primary_key=True
    )
    target_nation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nations.id"), primary_key=True
    )
    status: Mapped[str] = mapped_column(String(20), default=DiplomaticStatus.NEUTRAL)

    nation: Mapped["Nation"] = relationship(
        "Nation", foreign_keys=[nation_id], back_populates="diplomatic_stances"
    )
    target: Mapped["Nation"] = relationship("Nation", foreign_keys=[target_nation_id])
