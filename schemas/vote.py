from pydantic import BaseModel, field_validator

class VoteSchema(BaseModel):
    dish_id: int
    vote_type: str

    @field_validator("vote_type")
    def check_vote(cls, v):
        if v not in ["up", "down"]:
            raise ValueError("vote_type must be 'up' or 'down'")
        return v