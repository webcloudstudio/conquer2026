"""
Artifact model — rare items scattered across the map.

New system designed for the reboot; no direct C equivalent.
See the plan for the full artifact list and mechanics.
"""

import enum
import uuid

from sqlalchemy import Boolean, Float, ForeignKey, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Rarity(str, enum.Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    LEGENDARY = "legendary"


class EffectType(str, enum.Enum):
    MORALE_BONUS = "morale_bonus"
    CARAVAN_CAPACITY = "caravan_capacity"
    METAL_PRODUCTION = "metal_production"
    FOOD_PRODUCTION = "food_production"
    MAGIC_REGEN = "magic_regen"
    NAVAL_MOVEMENT = "naval_movement"
    COMBAT_EFFECTIVENESS = "combat_effectiveness"
    SCOUT_RANGE = "scout_range"
    DIPLOMATIC_GOODWILL = "diplomatic_goodwill"
    ENEMY_MORALE_PENALTY = "enemy_morale_penalty"
    WEATHER_IMMUNITY = "weather_immunity"
    ALL_PRODUCTION = "all_production"
    NO_DESERTION = "no_desertion"
    DRAGON_UNIT = "dragon_unit"
    VICTORY_POINTS_PER_TURN = "victory_points_per_turn"


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worlds.id"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="")
    effect_type: Mapped[str] = mapped_column(String(50), nullable=False)
    effect_value: Mapped[float] = mapped_column(Float, default=0.0)
    rarity: Mapped[str] = mapped_column(String(20), default=Rarity.COMMON)

    # Where the artifact is — either held by a nation or on the map
    holder_nation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nations.id"), nullable=True, index=True
    )
    sector_x: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    sector_y: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    is_guarded: Mapped[bool] = mapped_column(Boolean, default=False)
    is_revealed: Mapped[bool] = mapped_column(Boolean, default=False)  # discovered by any scout

    world: Mapped["World"] = relationship("World", back_populates="artifacts")  # noqa: F821
    holder_nation: Mapped["Nation | None"] = relationship(  # noqa: F821
        "Nation", back_populates="held_artifacts"
    )
