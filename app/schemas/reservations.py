from pydantic import BaseModel
import datetime

class ReservationBase(BaseModel):
    guest_id: int
    room_id: int
    check_in: datetime.datetime
    check_out: datetime.datetime
    status: str

class ReservationCreate(ReservationBase):
    pass

class ReservationOut(ReservationBase):
    id: int

    class Config:
        orm_mode = True