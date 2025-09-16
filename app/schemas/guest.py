from pydantic import BaseModel, EmailStr

class GuestBase(BaseModel):
    name: str
    email: EmailStr | None = None
    phone_number: str | None = None
    cpf: str

class GuestCreate(GuestBase):
    pass

class GuestOut(GuestBase):
    id: int

    class Config:
        orm_mode = True