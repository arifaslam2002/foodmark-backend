from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from auth import decode_token
from database import get_db
from models.feedback import Feedback
from models.shop import Shop
from models.user import User
from schemas.feedback import FeedbackCreateSchema, ReplySchema


router = APIRouter(prefix="/feedback", tags=["Owner Feedback"])

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token missing")
    token = authorization.split(" ")[1]
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return data
@router.post("/send")
def send_feedback(
    data:FeedbackCreateSchema,
    db:Session =Depends(get_db),
    current_user:dict = Depends(get_current_user)
):
    shop = db.query(Shop).filter(Shop.id == data.shop_id).first()
    if not shop:
        raise HTTPException(status_code=404,details="Shop not found")
    feedback = Feedback(
        shop_id = data.shop_id,
        user_id=current_user["user_id"],
        dish_id = data.dish_id,
        taste = data.taste,
        portion=data.portion,
        value=data.value,
        presentation=data.presentation,
        comment = data.comment
    )
    db.add(feedback)
    db.commit()
    return{"message":"Feedback sent to owner!"}
@router.get("/my-shop/{shop_id}")
def get_my_feedback(
    shop_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Only owners can view feedback")

    shop = db.query(Shop).filter(
        Shop.id       == shop_id,
        Shop.owner_id == current_user["user_id"]
    ).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found or not yours")

    # ✅ get ALL feedbacks for this shop — no user filter
    feedbacks = db.query(Feedback).filter(
        Feedback.shop_id == shop_id
    ).order_by(Feedback.created_at.desc()).all()

    for f in feedbacks:
        f.is_read = True
    db.commit()

    total = len(feedbacks)
    if total == 0:
        return {"message": "No feedback yet", "feedbacks": []}

    avg_taste        = round(sum(f.taste        for f in feedbacks) / total, 2)
    avg_portion      = round(sum(f.portion      for f in feedbacks) / total, 2)
    avg_value        = round(sum(f.value        for f in feedbacks) / total, 2)
    avg_presentation = round(sum(f.presentation for f in feedbacks) / total, 2)

    result = []
    for f in feedbacks:
        user = db.query(User).filter(User.id == f.user_id).first()
        result.append({
            "feedback_id" : f.id,                                          # ✅
            "from"        : user.name if user else "Unknown",              # ✅
            "dish_id"     : f.dish_id,
            "taste"       : f.taste,
            "portion"     : f.portion,
            "value"       : f.value,
            "presentation": f.presentation,
            "comment"     : f.comment,
            "owner_reply" : f.owner_reply if f.owner_reply else "No reply yet",
            "date"        : f.created_at
        })

    return {
        "total"    : total,
        "averages" : {
            "taste"       : avg_taste,
            "portion"     : avg_portion,
            "value"       : avg_value,
            "presentation": avg_presentation
        },
        "feedbacks": result
    }
@router.get("/unread/{shop_id}")
def unread_count(
    shop_id:int,
    db:Session =Depends(get_db),
    current_user:dict =Depends(get_current_user)
):
    if current_user["role"] != "owner":
        raise HTTPException(status_code=403,detail="Only owners can view this")
    count = db.query(Feedback).filter(
        Feedback.shop_id == shop_id,
        not Feedback.is_read
    ).count()
    return{"unread_feedback":count}
@router.post("/reply/{feedback_id}")
def reply_feedback(
    feedback_id: int,
    data: ReplySchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Only owners can reply")

    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    # make sure feedback belongs to this owner's shop
    shop = db.query(Shop).filter(
        Shop.id == feedback.shop_id,
        Shop.owner_id == current_user["user_id"]
    ).first()
    if not shop:
        raise HTTPException(status_code=403, detail="This feedback is not yours")

    feedback.owner_reply = data.reply
    db.commit()

    return {"message": "Reply sent!"}

@router.get("/my/{shop_id}")
def get_my_feedback_with_reply(
    shop_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    feedbacks = db.query(Feedback).filter(
        Feedback.shop_id  == shop_id,
        Feedback.user_id  == current_user["user_id"]
    ).order_by(Feedback.created_at.desc()).all()

    if not feedbacks:
        return {"message": "No feedback found", "feedbacks": []}

    result = []
    for f in feedbacks:
        result.append({
            "feedback_id" : f.id,
            "comment"     : f.comment,
            "taste"       : f.taste,
            "portion"     : f.portion,
            "value"       : f.value,
            "presentation": f.presentation,
            "owner_reply" : f.owner_reply if f.owner_reply else "No reply yet",
            "date"        : f.created_at
        })

    return {
        "total"    : len(result),
        "feedbacks": result
    }
