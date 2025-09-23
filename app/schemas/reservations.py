from pydantic import BaseModel, EmailStr

class ReservationBase(BaseModel):
    guest_id: int
    room_id: int
    check_in: str
    check_out: str
    status: str

class ReservationCreate(ReservationBase):
    pass

class ReservationOut(ReservationBase):
    id: int

    class Config:
        orm_mode = True