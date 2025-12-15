from pydantic import BaseModel, Field
from typing import Optional
import datetime

class ServicesBase(BaseModel):
    reservation_id: int
    guest_id: int
    room_id: int
    request: str
    status: str
    created_at: datetime.datetime

    class Config:
        orm_mode = True

class ServicesCreate(ServicesBase):
    pass

class ServicesOut(ServicesBase):
    id: int

    class Config:
        orm_mode = True