from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user
from app.models import Follow, Profile, User
from app.schemas import NetworkUser
from app.services.notify import notify
from app.services.profile import follow_counts

router = APIRouter(prefix="/network", tags=["network"])


def _to_network(db: Session, user: User, viewer: User | None) -> NetworkUser:
    followers, following = follow_counts(db, user.id)
    profile = user.profile or Profile(full_name=user.username)
    is_following = False
    if viewer:
        is_following = (
            db.query(Follow)
            .filter(Follow.follower_id == viewer.id, Follow.following_id == user.id)
            .first()
            is not None
        )
    return NetworkUser(
        id=user.id,
        username=user.username,
        full_name=profile.full_name,
        headline=profile.headline,
        photo_path=profile.photo_path or "",
        followers=followers,
        following=following,
        is_following=is_following,
    )


@router.get("/people", response_model=list[NetworkUser])
def people(
    q: str = "",
    db: Session = Depends(get_db),
    viewer: User | None = Depends(get_optional_user),
):
    query = db.query(User)
    term = q.strip().lower()
    if term:
        like = f"%{term}%"
        query = (
            query.outerjoin(Profile, Profile.user_id == User.id)
            .filter((User.username.ilike(like)) | (Profile.full_name.ilike(like)))
            .distinct()
        )
    users = query.order_by(User.created_at.desc()).limit(50).all()
    return [_to_network(db, user, viewer) for user in users]


@router.post("/follow/{username}", response_model=NetworkUser)
def toggle_follow(
    username: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    target = db.query(User).filter(User.username == username.lower()).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    if target.id == user.id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself.")
    existing = (
        db.query(Follow)
        .filter(Follow.follower_id == user.id, Follow.following_id == target.id)
        .first()
    )
    if existing:
        db.delete(existing)
    else:
        db.add(Follow(follower_id=user.id, following_id=target.id))
        notify(
            db,
            target.id,
            "follow",
            f"{user.username} started following you",
            "Open their profile to connect back.",
            f"/u/{user.username}",
        )
    db.commit()
    return _to_network(db, target, user)
