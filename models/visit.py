from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class Visit(Base):
    __tablename__ = "visits"

    id         = Column(Integer, primary_key=True, index=True)
    shop_id    = Column(Integer, ForeignKey("shops.id"), nullable=False)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())