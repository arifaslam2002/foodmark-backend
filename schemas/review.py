from typing import Optional

from pydantic import BaseModel, field_validator

class ReviewCreateSchema(BaseModel):
    shop_id: int
    dish_id : Optional[int] = None 
    comment: str
    rating: float
    user_lat: float
    user_lng: float

    @field_validator("rating")
    def check_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5")
        return v