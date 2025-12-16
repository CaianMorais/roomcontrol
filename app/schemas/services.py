from pydantic import BaseModel, Field
from typing import Optional, Literal
import datetime

class HotelOut(BaseModel):
    id: int
    name: str
    address: str
    city: str
    state: str
    zip_code: int
    phone_number: int
    email: str

    class Config:
        orm_mode = True

class RoomOut(BaseModel):
    id: int
    room_number: str
    price: float
    hotel: Optional[HotelOut]

    class Config:
        orm_mode = True

class GuestOut(BaseModel):
    id: int
    name: str
    cpf: str

    class Config:
        orm_mode = True

class ReservationOut(BaseModel):
    id: int
    guest: Optional[GuestOut]
    room: Optional[RoomOut]

    class Config:
        orm_mode = True


class ServicesBase(BaseModel):
    id: int
    request: str
    status: str
    created_at: datetime.datetime

    class Config:
        orm_mode = True

class ServicesCreate(ServicesBase):
    pass

class ServicesOut(ServicesBase):
    reservation: Optional[ReservationOut]

    class Config:
        orm_mode = True