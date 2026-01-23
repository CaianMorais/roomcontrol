import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr

class HotelBase(BaseModel):
    name: str
    login: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    cnpj: str

class HotelCreate(HotelBase):
    password: str = Field(..., min_length=8, example="securepassword")

class HotelOut(HotelBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_active: bool

class RegisterHotelStep1In(BaseModel):
    email: EmailStr
    cnpj: str

class RegisterHotelStep1Out(BaseModel):
    ok: bool
    message: str | None = None
    cnpj: str | None = None
    email: EmailStr | None = None

    class Config:
        orm_mode = True