from pydantic import BaseModel

class ReportCreateSchema(BaseModel):
    review_id: int
    reason   : str