import datetime
from pydantic import BaseModel, Field
from typing import Optional

class HotelOut(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone_number: Optional[str] = None

    class Config:
        orm_mode = True

class RoomsBase(BaseModel):
    room_number: str
    type: str
    capacity_adults: int
    capacity_children: int
    capacity_total: int
    price: Optional[float] = None
    status: Optional[str] = None
    comments: Optional[str] = None

class RoomCreate(RoomsBase):
    pass

class RoomOut(RoomsBase):
    id: int
    is_active: bool
    hotel: Optional[HotelOut] = None

    class Config:
        orm_mode = True
