from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from database import Base

class Rating(Base):
    __tablename__ = "rating"

    id          = Column(Integer, primary_key=True, index=True)
    shop_id     = Column(Integer, ForeignKey("shops.id"), nullable=False)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    service     = Column(Float, nullable=False)    # 1 to 5
    cleanliness = Column(Float, nullable=False)    # 1 to 5
    staff       = Column(Float, nullable=False)    # 1 to 5
    ambience    = Column(Float, nullable=False)    # 1 to 5
    created_at  = Column(DateTime, default=func.now())

    # one rating per user per shop
    __table_args__ = (UniqueConstraint("user_id", "shop_id", name="one_ambience_per_shop"),)