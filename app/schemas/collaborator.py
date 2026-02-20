from pydantic import BaseModel
import datetime
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

class CollaboratorBase(BaseModel):
    id: int
    firstname: str
    lastname: str
    cpf: str
    created_at: datetime.datetime

class CollaboratorCreate(BaseModel):
    pass

class CollaboratorOut(CollaboratorBase):
    is_active: bool
    hotel: Optional[HotelOut] = None

    class Config:
        orm_mode = True