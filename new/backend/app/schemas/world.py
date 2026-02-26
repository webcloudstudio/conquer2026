import uuid
from datetime import datetime

from pydantic import BaseModel


class WorldCreate(BaseModel):
    name: str
    mapx: int = 79
    mapy: int = 49


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

    model_config = {"from_attributes": True}


class AddCoAdminRequest(BaseModel):
    username: str
