from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from auth import decode_token
from database import get_db
from models.announcement import Announcement
from models.shop import Shop
from schemas.announcement import AnnouncementCreateSchema


router = APIRouter(prefix="/announcements", tags=["Shop Announcements"])

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token missing")
    token = authorization.split(" ")[1]
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return data
@router.post("/add")
def add_announcement(
    data: AnnouncementCreateSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "owner":
     raise HTTPException(status_code=403, detail="Only owners can post announcements")
    shop = db.query(Shop).filter(
        Shop.id == data.shop_id,
        Shop.owner_id == current_user["user_id"]
    ).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found or not yours")

    announcement = Announcement(
        shop_id = data.shop_id,
        title   = data.title,
        message = data.message
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return {"message": "Announcement posted!"}

@router.get("/{shop_id}")
def get_announcements(shop_id: int, db: Session = Depends(get_db)):
    announcements = db.query(Announcement).filter(
        Announcement.shop_id  == shop_id,
        Announcement.is_active == True
    ).order_by(Announcement.created_at.desc()).all()

    if not announcements:
        return {"message": "No announcements yet", "announcements": []}

    return {
        "total": len(announcements),
        "announcements": [
            {
                "id"        : a.id,
                "title"     : a.title,
                "message"   : a.message,
                "posted_at" : a.created_at
            }
            for a in announcements
        ]
    }
@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Only owners can delete announcements")

    announcement = db.query(Announcement).filter(
        Announcement.id == announcement_id
    ).first()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    announcement.is_active = False
    db.commit()
    return {"message": "Announcement removed!"}