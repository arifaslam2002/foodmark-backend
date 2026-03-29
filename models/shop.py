from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from database import Base

class Shop(Base):
    __tablename__ = "shops"

    id            = Column(Integer, primary_key=True, index=True)
    owner_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    name          = Column(String, nullable=False)
    description   = Column(String, nullable=True)
    address       = Column(String, nullable=False)
    latitude      = Column(Float, nullable=False)
    longitude     = Column(Float, nullable=False)
    cuisine_type  = Column(String, nullable=True)   # eg: Kerala, Chinese, Fast Food
    gst_number    = Column(String, nullable=True)
    fssai_number  = Column(String, nullable=True)
    district      = Column(String, nullable=True) 
    state         = Column(String, nullable=True)  
    country       = Column(String, default="India")
    open_time     = Column(String, nullable=True)   # ✅ new eg: "09:00"
    close_time    = Column(String, nullable=True)   # ✅ new eg: "22:00"
    open_days     = Column(String, nullable=True) 
    is_verified   = Column(Boolean, default=False)  # admin approves this
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=func.now())