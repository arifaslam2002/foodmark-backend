from pydantic import BaseModel
from typing import Optional

class DishOfDayCreateSchema(BaseModel):
    shop_id     : int
    dish_id     : int
    special_note: Optional[str] = None