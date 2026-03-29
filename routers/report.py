from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from auth import decode_token
from database import get_db
from models.report import Report
from models.review import Review
from models.user import User
from schemas.report import ReportCreateSchema


router = APIRouter(prefix="/reports", tags=["Report Fake Review"])
def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token missing")
    token = authorization.split(" ")[1]
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return data

@router.post("/add")
def report_review(
    data: ReportCreateSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    review = db.query(Review).filter(Review.id == data.review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # cant report your own review
    if review.user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="You cannot report your own review")
    
    report =Report(
        review_id   = data.review_id,
        reported_by = current_user["user_id"],
        reason      = data.reason
    )
    db.add(report)
    db.commit()
    report_count = db.query(Report).filter(
    Report.review_id == data.review_id
    ).count()
    if report_count >= 3:
      review.is_trusted =False
      db.commit()
      return {"message": "Review reported! It has been flagged for review."}


    return {
        "message"     : "Review reported!",
        "report_count": report_count
    }

@router.get("/all")
def get_all_reports(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view reports")

    reports = db.query(Report).filter(
        Report.is_resolved == False
    ).order_by(Report.created_at.desc()).all()

    if not reports:
        return {"message": "No reports found", "reports": []}

    result = []
    for r in reports:
        review  = db.query(Review).filter(Review.id == r.review_id).first()
        reporter = db.query(User).filter(User.id == r.reported_by).first()
        result.append({
            "report_id"  : r.id,
            "review_id"  : r.review_id,
            "comment"    : review.comment if review else "Deleted",
            "reported_by": reporter.name if reporter else "Unknown",
            "reason"     : r.reason,
            "date"       : r.created_at
        })

    return {"total": len(result), "reports": result}

@router.patch("/resolve/{report_id}")
def resolve_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can resolve reports")

    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.is_resolved = True
    db.commit()
    return {"message": "Report resolved!"}

@router.delete("/delete-review/{review_id}")
def delete_fake_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete reviews")

    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # ✅ delete reports first before deleting review
    db.query(Report).filter(Report.review_id == review_id).delete()
    db.commit()

    # now safe to delete review
    db.delete(review)
    db.commit()

    return {"message": "Fake review and its reports deleted!"}
