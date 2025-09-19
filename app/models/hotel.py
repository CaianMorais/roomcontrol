from sqlalchemy import Column, Integer, String, DateTime, func, Boolean
from app.core.config import Base

#   op.create_table(
#         'hotels',
#         sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
#         sa.Column('name', sa.String(100), nullable=False),
#         sa.Column('login', sa.String(50), nullable=False, unique=True),
#         sa.Column('password', sa.String(255), nullable=False),
#         sa.Column('address', sa.String(255), nullable=True),
#         sa.Column('city', sa.String(100), nullable=True),
#         sa.Column('state', sa.String(100), nullable=True),
#         sa.Column('zip_code', sa.String(20), nullable=True),
#         sa.Column('phone_number', sa.String(20), nullable=True),
#         sa.Column('email', sa.String(100), nullable=True),
#         sa.Column('cnpj', sa.String(20), nullable=False, unique=True),
#         sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now(), nullable=False),
#     )

class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    login = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    phone_number = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    cnpj = Column(String(20), nullable=False, unique=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)