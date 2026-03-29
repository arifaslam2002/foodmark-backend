from pydantic import BaseModel
from typing import Optional

class ShopCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None
    address: str
    latitude: float
    longitude: float
    cuisine_type: Optional[str] = None
    gst_number: Optional[str] = None
    fssai_number: Optional[str] = None
    district    : Optional[str] = None  
    state       : Optional[str] = None   
    country     : str = "India"
    open_time   : Optional[str] = None   # "09:00"
    close_time  : Optional[str] = None   # "22:00"
    open_days   : Optional[str] = None 
class ShopResponseSchema(BaseModel):
    id: int
    name: str
    description: Optional[str]
    address: str
    latitude: float
    longitude: float
    cuisine_type: Optional[str]
    district    : Optional[str]
    state       : Optional[str]
    country     : Optional[str]
    open_time   : Optional[str]   # "09:00"
    close_time  : Optional[str]   # "22:00"
    open_days   : Optional[str] 
    is_verified: bool

    class Config:
        from_attributes = True