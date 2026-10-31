from sqlalchemy.orm import Session

from app.models import Notification


def notify(
    db: Session,
    user_id: int,
    ntype: str,
    title: str,
    body: str = "",
    link: str = "",
) -> Notification:
    item = Notification(
        user_id=user_id, type=ntype, title=title, body=body, link=link
    )
    db.add(item)
    db.flush()
    return item
