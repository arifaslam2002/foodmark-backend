from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from database import Base

class Dish(Base):
    __tablename__ = "dishes"

    id          = Column(Integer, primary_key=True, index=True)
    shop_id     = Column(Integer, ForeignKey("shops.id"), nullable=False)
    name        = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price       = Column(Float, nullable=False)
    ingredients = Column(String, nullable=True)   # "rice, coconut, spices"
    is_veg      = Column(Boolean, default=True)
    is_available= Column(Boolean, default=True)
    is_vegan     = Column(Boolean, default=False)   # ✅ new
    is_gluten_free= Column(Boolean, default=False)  # ✅ new
    is_diabetic_friendly= Column(Boolean, default=False) # ✅ new
    spice_level  = Column(String, default="medium")
    created_at  = Column(DateTime, default=func.now())