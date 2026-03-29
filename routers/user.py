from fastapi import APIRouter,Depends, HTTPException
from auth import create_token, hash_password, verify_password
from models.user import User
from database import get_db
from schemas.user import LoginSchema, SignupSchema
from sqlalchemy.orm import Session

router = APIRouter(prefix="/users", tags=["Users"])
@router.post("/signup")
def signup(data:SignupSchema,db:Session =Depends(get_db)):
    existing = db.query(User).filter(User.phone == data.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone already registered")
    user = User(
        name=data.name,
        phone=data.phone,
        password=hash_password(data.password),  # noqa: F821
        role=data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Account created!", "user_id": user.id}
@router.post("/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == data.phone).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Wrong Phone or Password")

    token = create_token({"user_id": user.id, "role": user.role})

    return {
        "token": token,
        "role": user.role,
        "name": user.name,
        "user_id": user.id 
    }
