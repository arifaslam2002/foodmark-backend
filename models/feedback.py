from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from database import Base

class Feedback(Base):
    __tablename__ = "feedbacks"

    id           = Column(Integer, primary_key=True, index=True)
    shop_id      = Column(Integer, ForeignKey("shops.id"), nullable=False)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    dish_id      = Column(Integer, ForeignKey("dishes.id"), nullable=True)  # optional
    taste        = Column(Float, nullable=False)      # 1 to 5
    portion      = Column(Float, nullable=False)      # 1 to 5
    value        = Column(Float, nullable=False)      # 1 to 5
    presentation = Column(Float, nullable=False)      # 1 to 5
    comment      = Column(String, nullable=True)      # optional comment
    owner_reply  = Column(String, nullable=True) 
    is_read      = Column(Boolean, default=False)     # owner seen it?
    created_at   = Column(DateTime, default=func.now())