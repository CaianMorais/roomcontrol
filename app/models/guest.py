from sqlalchemy import Column, Integer, String
from app.core.config import Base

class Guest(Base):
    __tablename__ = "guests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    phone_number = Column(String(15), unique=True, index=True, nullable=True)
    cpf = Column(String(11), unique=True, index=True, nullable=False)