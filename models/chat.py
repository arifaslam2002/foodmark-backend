from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class Chat(Base):
    __tablename__ = "chats"

    id         = Column(Integer, primary_key=True, index=True)
    dish_id    = Column(Integer, ForeignKey("dishes.id"), nullable=False)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    message    = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())