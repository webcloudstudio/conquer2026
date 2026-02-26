"""
WorldEvent model — random events that fire each turn.

New system designed for the reboot. Events affect one or more sectors,
persist for multiple turns, and can chain into follow-on events.
"""

import uuid
import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class EventCategory(str, enum.Enum):
    WEATHER = "weather"
    GEOLOGICAL = "geological"
    SOCIAL = "social"
    MAGICAL = "magical"


class EventType(str, enum.Enum):
    # Weather
    BLIZZARD = "blizzard"
    DROUGHT = "drought"
    FLOOD = "flood"
    FOG_BANK = "fog_bank"
    PERFECT_GROWING_SEASON = "perfect_growing_season"
    HARSH_WINTER = "harsh_winter"
    MONSOON = "monsoon"
    # Geological
    EARTHQUAKE = "earthquake"
    VOLCANIC_ERUPTION = "volcanic_eruption"
    LANDSLIDE = "landslide"
    TREASURE_STRIKE = "treasure_strike"
    SPRING_THAW = "spring_thaw"
    SINKHOLE = "sinkhole"
    # Social
    PLAGUE = "plague"
    PEASANT_UPRISING = "peasant_uprising"
    GOLDEN_AGE = "golden_age"
    MERCENARY_BAND = "mercenary_band"
    PIRATE_RAID = "pirate_raid"
    DESERTION_WAVE = "desertion_wave"
    TRADE_FAIR = "trade_fair"
    # Magical
    LEY_LINE_SURGE = "ley_line_surge"
    ANCIENT_RUINS = "ancient_ruins"
    WANDERING_DRAGON = "wandering_dragon"
    CURSE_OF_ANCIENTS = "curse_of_ancients"
    MAGICAL_STORM = "magical_storm"
    PROPHET_RISES = "prophet_rises"


class WorldEvent(Base):
    __tablename__ = "world_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worlds.id"), nullable=False, index=True
    )

    # Optional: event targets a specific nation (social/magical events)
    target_nation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nations.id"), nullable=True
    )

    # Chain linkage
    chain_parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("world_events.id"), nullable=True
    )

    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)

    # List of [x, y] pairs this event affects
    affected_sectors: Mapped[list] = mapped_column(JSONB, default=list)

    turns_remaining: Mapped[int] = mapped_column(SmallInteger, default=1)
    severity: Mapped[int] = mapped_column(Integer, default=1)  # 1=mild, 5=catastrophic
    display_icon: Mapped[str] = mapped_column(String(50), default="")

    # Extra data specific to the event type (e.g., mercenary army strength)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    world: Mapped["World"] = relationship("World", back_populates="events")  # noqa: F821
    target_nation: Mapped["Nation | None"] = relationship("Nation")  # noqa: F821
    chain_parent: Mapped["WorldEvent | None"] = relationship(
        "WorldEvent", remote_side="WorldEvent.id"
    )
