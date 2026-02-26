import uuid
from datetime import datetime

from pydantic import BaseModel


class WorldCreate(BaseModel):
    name: str
    mapx: int = 79
    mapy: int = 49
    pwater: int = 35
    pmount: int = 20
    npc_count: int = 8
    seed: int | None = None
    max_players: int = 20


class WorldAdminInfo(BaseModel):
    user_id: uuid.UUID
    username: str


class WorldOut(BaseModel):
    id: uuid.UUID
    name: str
    mapx: int
    mapy: int
    turn: int
    is_active: bool
    is_maintenance: bool
    created_at: datetime
    admins: list[WorldAdminInfo] = []
    max_players: int = 20
    player_count: int = 0

    model_config = {"from_attributes": True}


class AddCoAdminRequest(BaseModel):
    username: str
