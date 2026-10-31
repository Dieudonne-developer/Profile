from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Notification, User
from app.schemas import NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(user: User = Depends(get_current_user)):
    return sorted(user.notifications, key=lambda item: item.created_at, reverse=True)


@router.get("/unread-count")
def unread_count(user: User = Depends(get_current_user)):
    return {"count": sum(1 for item in user.notifications if not item.is_read)}


@router.post("/read-all")
def read_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    for item in user.notifications:
        item.is_read = True
    db.commit()
    return {"ok": True}


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = db.get(Notification, notification_id)
    if item and item.user_id == user.id:
        item.is_read = True
        db.commit()
        db.refresh(item)
        return item
    raise HTTPException(status_code=404, detail="Notification not found.")
