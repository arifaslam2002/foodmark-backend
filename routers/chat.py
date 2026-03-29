from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from auth import decode_token
from database import SessionLocal, get_db
from models.chat import Chat
from models.user import User

router = APIRouter(prefix="/chat", tags=["Talk Box"])

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token missing")
    token = authorization.split(" ")[1]
    data = decode_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return data

class ConnectionManager:
    def __init__(self):
        self.active = {}

    async def connect(self, dish_id: int, websocket: WebSocket):
        await websocket.accept()
        if dish_id not in self.active:
            self.active[dish_id] = []
        self.active[dish_id].append(websocket)  # ✅ bug 1 fix — was inside if block

    def disconnect(self, dish_id: int, websocket: WebSocket):  # ✅ bug 2 fix — was missing
        if dish_id in self.active:
            self.active[dish_id].remove(websocket)

    async def broadcast(self, dish_id: int, message: str):
        if dish_id in self.active:
            for connection in self.active[dish_id]:
                await connection.send_text(message)  # ✅ bug 3 fix — was "self.connection"

manager = ConnectionManager()

@router.websocket("/ws/{dish_id}/{token}")
async def websocket_chat(dish_id: int, token: str, websocket: WebSocket):
    data = decode_token(token)
    if not data:
        await websocket.close()
        return

    db = SessionLocal()
    user = db.query(User).filter(User.id == data["user_id"]).first()
    if not user:
        await websocket.close()
        return

    await manager.connect(dish_id, websocket)
    try:
        while True:
            message = await websocket.receive_text()
            chat = Chat(
                dish_id=dish_id,
                user_id=user.id,
                message=message
            )
            db.add(chat)
            db.commit()
            await manager.broadcast(
                dish_id,
                f"{user.name}: {message}"
            )
    except WebSocketDisconnect:
        manager.disconnect(dish_id, websocket)
    finally:
        db.close()

@router.get("/history/{dish_id}")
def get_history(dish_id: int, db: Session = Depends(get_db)):
    chats = db.query(Chat).filter(
        Chat.dish_id == dish_id
    ).order_by(Chat.created_at).all()

    result = []
    for c in chats:
        user = db.query(User).filter(User.id == c.user_id).first()
        result.append({
            "user_id"   : c.user_id,      # ✅ add this
            "user"      : user.name if user else "Unknown",
            "message"   : c.message,
            "created_at": c.created_at
        })
    return result