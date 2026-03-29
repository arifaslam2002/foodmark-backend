from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class DishJourney(Base):
    __tablename__ = "dish_journey"

    id         = Column(Integer, primary_key=True, index=True)
    dish_id    = Column(Integer, ForeignKey("dishes.id"), nullable=False)
    shop_id    = Column(Integer, ForeignKey("shops.id"), nullable=False)
    note       = Column(String, nullable=False)   # eg: "reduced spice level"
    created_at = Column(DateTime, default=func.now())