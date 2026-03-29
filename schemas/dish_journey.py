from pydantic import BaseModel

class DishJourneyCreateSchema(BaseModel):
    dish_id: int
    note   : str