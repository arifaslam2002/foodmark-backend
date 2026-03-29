from pydantic import BaseModel, field_validator

class ConsensusVoteSchema(BaseModel):
    dish_id: int
    vote   : str

    @field_validator("vote")
    def check_vote(cls, v):
        if v not in ["yes", "no"]:
            raise ValueError("Vote must be 'yes' or 'no'")
        return v