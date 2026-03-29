from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from database import Base

class UserBadge(Base):
    __tablename__ = "user_badges"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    dish_id    = Column(Integer, ForeignKey("dishes.id"), nullable=False)
    badge_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # one badge per user per dish
    __table_args__ = (UniqueConstraint("user_id", "dish_id", name="one_userbadge_per_dish"),)