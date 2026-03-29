from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from database import Base

class Vote(Base):
    __tablename__ = "votes"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    dish_id    = Column(Integer, ForeignKey("dishes.id"), nullable=False)
    vote_type  = Column(String, nullable=False)   # "up" or "down"
    created_at = Column(DateTime, default=func.now())

    # one vote per user per dish
    __table_args__ = (UniqueConstraint("user_id", "dish_id", name="one_vote_per_dish"),)