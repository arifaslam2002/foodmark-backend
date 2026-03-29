from pydantic import BaseModel, field_validator
from typing import Optional

class FeedbackCreateSchema(BaseModel):
    shop_id     : int
    dish_id     : Optional[int] = None
    taste       : float
    portion     : float
    value       : float
    presentation: float
    comment     : Optional[str] = None

    @field_validator("taste", "portion", "value", "presentation")
    def check_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5")
        return v
class ReplySchema(BaseModel):
    reply: str