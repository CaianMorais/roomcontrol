from pydantic import BaseModel
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

class GuestBase(BaseModel):
    name: str
    email: str | None = None
    phone_number: str | None = None
    cpf: str

class GuestCreate(GuestBase):
    pass

class GuestOut(GuestBase):
    id: int
    hotel: Optional[HotelOut] = None

    class Config:
        orm_mode = True