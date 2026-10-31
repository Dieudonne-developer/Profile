"""Load resume.json and the profile photo into PostgreSQL."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from secrets import token_urlsafe

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import (
    Education,
    Experience,
    Follow,
    Language,
    Profile,
    Project,
    Skill,
    User,
)
from app.services.notify import notify

ROOT = Path(__file__).resolve().parent
RESUME_PATH = ROOT / "data" / "resume.json"
def _find_photo() -> Path | None:
    public = ROOT.parent / "profile-web-app" / "public" / "avatar.jpg"
    if public.exists():
        return public
    uploads = ROOT / "app" / "static" / "uploads" / "avatar.jpg"
    if uploads.exists():
        return uploads
    assets = Path(
        r"C:\Users\Dieudonne\.cursor\projects\d-Subjects-Python-Practical-Profile\assets"
    )
    if assets.exists():
        matches = list(assets.glob("*.jpg")) + list(assets.glob("*.jpeg"))
        if matches:
            return matches[0]
    return None


def _upsert_user(db: Session, email: str, username: str, password: str, full_name: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(
            email=email,
            username=username,
            hashed_password=hash_password(password),
        )
        db.add(user)
        db.flush()
    else:
        user.email = email
        user.hashed_password = hash_password(password)
    profile = user.profile or db.query(Profile).filter(Profile.user_id == user.id).first()
    if not profile:
        profile = Profile(
            user_id=user.id,
            full_name=full_name,
            share_token=token_urlsafe(16),
        )
        db.add(profile)
        db.flush()
    user.profile = profile
    return user


def seed_from_resume(db: Session, data: dict) -> User:
    user = _upsert_user(
        db,
        data["email"].lower(),
        data["username"].lower(),
        data["password"],
        data["full_name"],
    )
    profile = user.profile
    for field in (
        "full_name",
        "headline",
        "bio",
        "location",
        "phone",
        "public_email",
        "website",
        "github",
        "linkedin",
        "twitter",
        "birthday",
        "is_public",
    ):
        setattr(profile, field, data.get(field, getattr(profile, field)))

    photo = _find_photo()
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    if photo:
        named = settings.upload_dir / f"user-{user.id}.jpg"
        alias = settings.upload_dir / "avatar.jpg"
        shutil.copyfile(photo, named)
        shutil.copyfile(photo, alias)
        profile.photo_path = named.name

    db.query(Experience).filter(Experience.user_id == user.id).delete()
    db.query(Education).filter(Education.user_id == user.id).delete()
    db.query(Skill).filter(Skill.user_id == user.id).delete()
    db.query(Language).filter(Language.user_id == user.id).delete()
    db.query(Project).filter(Project.user_id == user.id).delete()

    for index, item in enumerate(data.get("experience", [])):
        db.add(Experience(user_id=user.id, sort_order=index, **item))
    for index, item in enumerate(data.get("education", [])):
        db.add(Education(user_id=user.id, sort_order=index, **item))
    for item in data.get("skills", []):
        db.add(Skill(user_id=user.id, **item))
    for item in data.get("languages", []):
        db.add(Language(user_id=user.id, **item))
    for index, item in enumerate(data.get("projects", [])):
        db.add(Project(user_id=user.id, sort_order=index, **item))
    return user


def seed_guest(db: Session, host: User) -> User:
    guest = _upsert_user(
        db,
        "guest@portfolio.local",
        "guest",
        "Guest12345!",
        "Alex Guest",
    )
    guest.profile.headline = "Product designer exploring the network"
    guest.profile.bio = (
        "Demo visitor account so you can try follows, likes, comments, and notifications."
    )
    guest.profile.is_public = True
    if not guest.projects:
        db.add(
            Project(
                user_id=guest.id,
                title="Design system exploration",
                summary="A compact UI kit used to demo likes, comments, and the project feed.",
                description="Companion demo work so visitors can interact with networking features on this portfolio.",
                tags=["UI", "Demo"],
                featured=False,
            )
        )
    existing = (
        db.query(Follow)
        .filter(Follow.follower_id == guest.id, Follow.following_id == host.id)
        .first()
    )
    if not existing:
        db.add(Follow(follower_id=guest.id, following_id=host.id))
        notify(
            db,
            host.id,
            "follow",
            "guest started following you",
            "Open their profile to connect back.",
            "/u/guest",
        )
    return guest


def _ensure_schema() -> None:
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    if "profiles" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("profiles")}
    if "birthday" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE profiles ADD COLUMN birthday VARCHAR(40) DEFAULT '2002-01-01'")
            )


def main() -> None:
    _ensure_schema()
    data = json.loads(RESUME_PATH.read_text(encoding="utf-8"))
    db = SessionLocal()
    try:
        host = seed_from_resume(db, data)
        seed_guest(db, host)
        db.commit()
        print(f"Seeded profile @{host.username} ({data['email']})")
        print("Password for Ntarindwa Jean Dieudonne:", data["password"])
        print("Demo network user: guest@portfolio.local / Guest12345!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
