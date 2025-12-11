import datetime
from pydantic import BaseModel, Field, EmailStr

class HotelBase(BaseModel):
    name: str
    login: str
    address: str
    city: str
    state: str
    zip_code: str
    phone_number: str
    email: EmailStr
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