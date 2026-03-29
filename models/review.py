from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from database import Base

class Review(Base):
    __tablename__ = "reviews"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    shop_id    = Column(Integer, ForeignKey("shops.id"), nullable=False)
    dish_id    = Column(Integer, ForeignKey("dishes.id"), nullable=True)
    comment    = Column(String, nullable=False)
    rating     = Column(Float, nullable=False)        # 1 to 5
    is_trusted = Column(Boolean, default=False)       # within 100 meters?
    user_lat   = Column(Float, nullable=False)        # where user was
    user_lng   = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())