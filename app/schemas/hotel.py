from pydantic import BaseModel, Field, EmailStr

class HotelBase(BaseModel):
    name: str = Field(..., example="Grand Plaza")
    login: str = Field(..., example="grandplaza")
    address: str = Field(..., example="123 Main St, Cityville")
    city: str = Field(..., example="Cityville")
    state: str = Field(..., example="Stateburg")
    zip_code: str = Field(..., example="12345")
    phone_number: str = Field(None, example="+1234567890")
    email: EmailStr = Field(None, example="info@grandplaza.com")
    cnpj: str = Field(..., example="12.345.678/0001-99")

class HotelCreate(HotelBase):
    password: str = Field(..., min_length=8, example="securepassword")

class HotelOut(HotelBase):
    id: int

    class Config:
        orm_mode = True