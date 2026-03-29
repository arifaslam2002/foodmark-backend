from pydantic import BaseModel, field_validator
from typing import Optional

class DishCreateSchema(BaseModel):
    shop_id             : int
    name                : str
    description         : Optional[str] = None
    price               : float
    ingredients         : Optional[str] = None
    is_veg              : bool = True
    is_vegan            : bool = False
    is_gluten_free      : bool = False
    is_diabetic_friendly: bool = False
    spice_level         : str  = "medium"

    @field_validator("spice_level")
    def check_spice(cls, v):
        if v not in ["mild", "medium", "spicy"]:
            raise ValueError("spice_level must be mild, medium or spicy")
        return v

class DishResponseSchema(BaseModel):
    id                  : int
    shop_id             : int
    name                : str
    description         : Optional[str]
    price               : float
    ingredients         : Optional[str]
    is_veg              : bool
    is_available        : bool
    is_vegan            : bool = False
    is_gluten_free      : bool = False
    is_diabetic_friendly: bool = False
    spice_level         : str  = "medium"

    class Config:
        from_attributes = True