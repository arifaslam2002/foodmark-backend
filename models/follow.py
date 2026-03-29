from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from database import Base

class Follow(Base):
    __tablename__ = "follows"

    id          = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # who follows
    following_id= Column(Integer, ForeignKey("users.id"), nullable=False)  # who is followed
    created_at  = Column(DateTime, default=func.now())

    # cant follow same person twice
    __table_args__ = (UniqueConstraint("follower_id", "following_id", name="one_follow"),)