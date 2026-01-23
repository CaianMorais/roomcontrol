from pydantic import BaseModel
import datetime
from typing import Optional

class GuestOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class HotelOut(BaseModel):
    id: int
    name: str
    cnpj: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

    class Config:
        orm_mode = True

class RoomsOut(BaseModel):
    id: int
    room_number: str
    price: Optional[float] = None
    hotel: Optional[HotelOut] = None

    class Config:
        orm_mode = True

class ReservationBase(BaseModel):
    id: int
    check_in: datetime.datetime
    check_out: datetime.datetime
    status: str

class ReservationCreate(ReservationBase):
    pass

class ReservationOut(ReservationBase):
    guest: Optional[GuestOut] = None
    room: Optional[RoomsOut] = None

    class Config:
        orm_mode = True