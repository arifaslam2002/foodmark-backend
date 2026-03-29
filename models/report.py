from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.sql import func
from database import Base

class Report(Base):
    __tablename__ = "reports"

    id          = Column(Integer, primary_key=True, index=True)
    review_id   = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason      = Column(String, nullable=False)
    is_resolved = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=func.now())

    # one report per user per review
    __table_args__ = (UniqueConstraint("review_id", "reported_by", name="one_report_per_review"),)