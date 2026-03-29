from pydantic import BaseModel, field_validator

class RatingCreateSchema(BaseModel):
    shop_id    : int
    service    : float
    cleanliness: float
    staff      : float
    ambience   : float

    @field_validator("service", "cleanliness", "staff", "ambience")
    def check_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5")
        return v