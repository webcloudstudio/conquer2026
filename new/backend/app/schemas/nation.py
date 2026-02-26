import uuid

from pydantic import BaseModel

from app.models.nation import PlayerClass, Race


class NationCreate(BaseModel):
    name: str
    leader_title: str = "Leader"
    race: Race = Race.HUMAN
    player_class: PlayerClass = PlayerClass.EMPIRE_BUILDER


class NationOut(BaseModel):
    id: uuid.UUID
    world_id: uuid.UUID
    name: str
    leader_title: str
    race: str
    player_class: str
    mark: str
    capital_x: int
    capital_y: int
    score: int
    victory_points: int
    is_npc: bool
    is_active: bool

    # Resource snapshot
    talons: int
    jewels: int
    metals: int
    food: int
    wood: int

    # Aggregates
    total_civilians: int
    total_military: int
    total_sectors: int

    model_config = {"from_attributes": True}
