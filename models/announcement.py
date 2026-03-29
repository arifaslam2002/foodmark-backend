from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from database import Base

class Announcement(Base):
    __tablename__ = "announcements"

    id         = Column(Integer, primary_key=True, index=True)
    shop_id    = Column(Integer, ForeignKey("shops.id"), nullable=False)
    title      = Column(String, nullable=False)
    message    = Column(String, nullable=False)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())