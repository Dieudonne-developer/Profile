from collections import defaultdict
from datetime import datetime, timedelta, timezone
from hashlib import sha256

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import AnalyticsEvent, User
from app.schemas import TrackIn

router = APIRouter(prefix="/analytics", tags=["analytics"])


def visitor_hash(request: Request) -> str:
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    return sha256(f"{ip}|{ua}".encode()).hexdigest()[:32]


@router.post("/track")
def track(
    payload: TrackIn,
    request: Request,
    db: Session = Depends(get_db),
):
    owner_username = payload.username.lower()
    owner = db.query(User).filter(User.username == owner_username).first()
    if not owner:
        return {"ok": False}
    event_type = payload.event_type if payload.event_type in {"profile_view", "cv_download", "share"} else "profile_view"
    event = AnalyticsEvent(
        owner_id=owner.id,
        event_type=event_type,
        visitor_hash=visitor_hash(request),
        path=payload.path or "",
        meta={"referrer": payload.referrer or request.headers.get("referer", "")},
    )
    db.add(event)
    db.commit()
    return {"ok": True}


@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    since = datetime.now(timezone.utc) - timedelta(days=30)
    rows = (
        db.query(AnalyticsEvent)
        .filter(AnalyticsEvent.owner_id == user.id, AnalyticsEvent.created_at >= since)
        .all()
    )
    by_type = defaultdict(int)
    by_day = defaultdict(int)
    uniques = set()
    for row in rows:
        by_type[row.event_type] += 1
        day = row.created_at.date().isoformat() if row.created_at else "unknown"
        by_day[day] += 1
        uniques.add(row.visitor_hash)
    days = []
    for offset in range(13, -1, -1):
        day = (datetime.now(timezone.utc) - timedelta(days=offset)).date().isoformat()
        days.append({"date": day, "count": by_day.get(day, 0)})
    return {
        "total": len(rows),
        "unique_visitors": len(uniques),
        "by_type": dict(by_type),
        "last_14_days": days,
        "cv_downloads": by_type.get("cv_download", 0),
        "profile_views": by_type.get("profile_view", 0),
        "shares": by_type.get("share", 0),
    }
