from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from database import Base

class Consensus(Base):
    __tablename__ = "consensus"

    id         = Column(Integer, primary_key=True, index=True)
    dish_id    = Column(Integer, ForeignKey("dishes.id"), nullable=False)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    vote       = Column(String, nullable=False)    # "yes" or "no"
    created_at = Column(DateTime, default=func.now())

    # one vote per user per dish
    __table_args__ = (UniqueConstraint("user_id", "dish_id", name="one_consensus_per_dish"),)