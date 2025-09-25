from pydantic import BaseModel, EmailStr
from typing import Optional

class GuestBase(BaseModel):
    name: str
    email: str | None = None
    phone_number: str | None = None
    cpf: str

class GuestCreate(GuestBase):
    pass

class GuestOut(GuestBase):
    id: int

    class Config:
        orm_mode = True