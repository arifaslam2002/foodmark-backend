from pydantic import BaseModel

class AnnouncementCreateSchema(BaseModel):
    shop_id : int
    title   : str
    message : str