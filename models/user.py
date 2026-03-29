from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, nullable=False)
    phone       = Column(String, unique=True, nullable=False)
    password    = Column(String, nullable=False)
    role        = Column(String, default="customer")  # customer / owner / admin
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=func.now())