from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import ContactMessage, User
from app.schemas import ContactIn, ContactOut
from app.services.email import send_contact_email
from app.services.notify import notify

router = APIRouter(prefix="/contact", tags=["contact"])


@router.get("/inbox", response_model=list[ContactOut])
def inbox(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(ContactMessage)
        .filter(ContactMessage.owner_id == user.id)
        .order_by(ContactMessage.created_at.desc())
        .all()
    )


@router.post("/{username}/read/{message_id}", response_model=ContactOut)
def mark_read(
    username: str,
    message_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.username != username.lower():
        raise HTTPException(status_code=403, detail="You can only read your own inbox.")
    item = (
        db.query(ContactMessage)
        .filter(ContactMessage.id == message_id, ContactMessage.owner_id == user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Message not found.")
    item.is_read = True
    db.commit()
    db.refresh(item)
    return item


@router.post("/{username}", response_model=ContactOut, status_code=201)
def send_message(username: str, payload: ContactIn, db: Session = Depends(get_db)):
    owner = db.query(User).filter(User.username == username.lower()).first()
    if not owner or not owner.profile or not owner.profile.is_public:
        raise HTTPException(status_code=404, detail="This profile is not accepting messages.")
    item = ContactMessage(
        owner_id=owner.id,
        sender_name=payload.name.strip(),
        sender_email=str(payload.email).lower(),
        subject=(payload.subject or "Portfolio contact").strip() or "Portfolio contact",
        body=payload.message.strip(),
    )
    db.add(item)
    notify(
        db,
        owner.id,
        "contact",
        f"Message from {item.sender_name}",
        item.body[:240],
        "/app/messages",
    )
    db.commit()
    db.refresh(item)
    try:
        send_contact_email(owner, item)
    except Exception as exc:
        print(f"gmail notify failed: {exc}")
    return item
