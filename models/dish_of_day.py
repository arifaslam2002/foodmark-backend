from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date
from sqlalchemy.sql import func
from database import Base

class DishOfDay(Base):
    __tablename__ = "dish_of_day"

    id          = Column(Integer, primary_key=True, index=True)
    shop_id     = Column(Integer, ForeignKey("shops.id"), nullable=False)
    dish_id     = Column(Integer, ForeignKey("dishes.id"), nullable=False)
    special_note= Column(String, nullable=True)   # eg: "20% off today only!"
    date        = Column(Date, default=func.current_date())
    created_at  = Column(DateTime, default=func.now())