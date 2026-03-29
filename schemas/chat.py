from pydantic import BaseModel

class ChatSchema(BaseModel):
    dish_id: int
    message: str