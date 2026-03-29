from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from auth import decode_token
from database import get_db
from models.consensus import Consensus
from models.dish import Dish
from schemas.consensus import ConsensusVoteSchema


router = APIRouter(prefix="/consensus", tags=["Consensus Meter"])
def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token missing")
    token = authorization.split(" ")[1]
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return data
@router.post("/vote")
def vote_consensus(
    data: ConsensusVoteSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    dish = db.query(Dish).filter(Dish.id == data.dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")
    existing = db.query(Consensus).filter(
    Consensus.user_id == current_user["user_id"],
    Consensus.dish_id == data.dish_id
    ).first()
    if existing:
        if existing.vote == data.vote:
            raise HTTPException(status_code=400, detail=f"You already voted {data.vote}")
        existing.vote = data.vote
        db.commit()
        return {"message": "Vote changed!"}
    consensus = Consensus(
        dish_id = data.dish_id,
        user_id = current_user["user_id"],
        vote    = data.vote
    )
    db.add(consensus)
    db.commit()
    return {"message": f"Voted {data.vote}!"}


@router.get("/result/{dish_id}")
def get_consensus(dish_id: int, db: Session = Depends(get_db)):
    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")

    yes_count = db.query(Consensus).filter(
        Consensus.dish_id == dish_id,
        Consensus.vote    == "yes"
    ).count()

    no_count = db.query(Consensus).filter(
        Consensus.dish_id == dish_id,
        Consensus.vote    == "no"
    ).count()

    total = yes_count + no_count

    # ✅ return safely when no votes
    if total == 0:
        return {
            "dish"       : dish.name,
            "total_votes": 0,
            "yes"        : 0,
            "no"         : 0,
            "yes_percent": 0,
            "no_percent" : 0,
            "message"    : "No votes yet"
        }

    yes_percent = round((yes_count / total) * 100, 1)
    no_percent  = round((no_count  / total) * 100, 1)

    if yes_percent >= 70:   verdict = "✅ Worth ordering!"
    elif yes_percent >= 50: verdict = "🤔 Mixed opinions"
    else:                   verdict = "❌ Not recommended"

    return {
        "dish"       : dish.name,
        "total_votes": total,
        "yes"        : yes_count,
        "no"         : no_count,
        "yes_percent": yes_percent,
        "no_percent" : no_percent,
        "verdict"    : verdict
    }