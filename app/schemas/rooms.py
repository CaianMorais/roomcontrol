import datetime
from pydantic import BaseModel, Field

class RoomsBase(BaseModel):
    hotel_id: str = Field(..., example="1")
    room_number: str = Field(..., example="302")
    type: str = Field(..., example="Suíte Luxo")
    capacity_adults: str = Field(..., example="2")
    capacity_children: str = Field(..., example="1")
    capacity_total: str = Field(..., example="3")
    price: str = Field(None, example="200.00")
    status : str = Field(None, example="available")
    comments: str = Field(..., example="Esse é um quarto de hotel.")

class RoomCreate(RoomsBase):
    pass

class RoomOut(RoomsBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_active: bool

    class Config:
        orm_mode = True
