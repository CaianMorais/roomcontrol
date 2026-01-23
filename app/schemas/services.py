from pydantic import BaseModel, EmailStr
from typing import Optional
import datetime

class HotelOut(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None

    class Config:
        orm_mode = True

class RoomOut(BaseModel):
    id: int
    room_number: str
    price: Optional[float] = None
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