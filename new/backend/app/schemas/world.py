import uuid
from datetime import datetime
from pydantic import BaseModel


class WorldCreate(BaseModel):
    name: str
    mapx: int = 79
    mapy: int = 49


class WorldOut(BaseModel):
    id: uuid.UUID
    name: str
    mapx: int
    mapy: int
    turn: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
