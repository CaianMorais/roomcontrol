from pydantic import BaseModel, Field, computed_field
from typing import Optional, Literal
import datetime

StatusType = Literal["pending", "in_progress", "completed"]

STATUS_LABEL = {
    "pending": "Pendente",
    "in_progress": "Em andamento",
    "completed": "Concluído",
}
DATE_FORMAT = ""

class TableHotelOut(BaseModel):
    id: int

    class Config:
        orm_mode = True

class TableRoomOut(BaseModel):
    room_number: str
    hotel: Optional[TableHotelOut]

    class Config:
        orm_mode = True

class TableGuestOut(BaseModel):
    name: str

    class Config:
        orm_mode = True

class TableReservationOut(BaseModel):
    id: int
    guest: Optional[TableGuestOut]
    room: Optional[TableRoomOut]

    class Config:
        orm_mode = True


class TableServicesBase(BaseModel):
    id: int
    status: StatusType
    created_at: datetime.datetime

    class Config:
        orm_mode = True

class TableServicesCreate(TableServicesBase):
    pass

class TableServicesOut(TableServicesBase):
    reservation: Optional[TableReservationOut]

    @computed_field
    @property
    def status_table(self) -> str:
        return STATUS_LABEL.get(self.status, self.status)
    
    @computed_field
    @property
    def request_date_table(self) -> str:
        return self.created_at.strftime("%d/%m/%Y %H:%M") if self.created_at else "—"

    class Config:
        orm_mode = True