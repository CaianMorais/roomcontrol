from sqlalchemy import Column, Integer, String, Float
from app.core.config import Base

class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    login = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    city = Column(String(255), nullable=False)
    state = Column(String(255), nullable=False)
    zip_code = Column(String(255), nullable=False)
    phone_number = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    cnpj = Column(String(20), unique=True, nullable=False)