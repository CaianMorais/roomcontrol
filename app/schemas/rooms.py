import datetime
from pydantic import BaseModel, Field
from typing import Optional

class RoomsBase(BaseModel):
    hotel_id: int = Field(..., example=1)
    room_number: str = Field(..., example="302")
    type: str = Field(..., example="Suíte Luxo")
    capacity_adults: int = Field(..., example=2)
    capacity_children: int = Field(..., example=1)
    capacity_total: int = Field(..., example=3)
    price: Optional[float] = Field(None, example=200.00)
    status: Optional[str] = Field("available", example="available")
    comments: Optional[str] = Field(None, example="Esse é um quarto de hotel.")

class RoomCreate(RoomsBase):
    pass

class RoomOut(RoomsBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_active: bool

    class Config:
        orm_mode = True
