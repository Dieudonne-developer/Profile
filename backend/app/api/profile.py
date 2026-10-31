from pathlib import Path
from secrets import token_urlsafe

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user
from app.models import Education, Experience, Language, Profile, Skill, User
from app.schemas import (
    EducationIn,
    EducationOut,
    ExperienceIn,
    ExperienceOut,
    LanguageIn,
    LanguageOut,
    ProfileOut,
    ProfileUpdate,
    PublicProfile,
    SkillIn,
    SkillOut,
    UserOut,
)
from app.services.profile import public_bundle

router = APIRouter(tags=["profile"])


def _profile_out(profile: Profile, username: str) -> ProfileOut:
    data = ProfileOut.model_validate(profile)
    data.username = username
    data.photo_path = profile.photo_path
    return data


def _public_profile(db, user: User, viewer: User | None) -> PublicProfile:
    bundle = public_bundle(db, user, viewer)
    return PublicProfile(
        user=UserOut.model_validate(user),
        profile=_profile_out(user.profile, user.username),
        experiences=bundle["experiences"],
        education=bundle["education"],
        skills=bundle["skills"],
        languages=bundle["languages"],
        projects=bundle["projects"],
        followers=bundle["followers"],
        following=bundle["following"],
        is_following=bundle["is_following"],
    )


@router.get("/profile/me", response_model=ProfileOut)
def my_profile(user: User = Depends(get_current_user)):
    return _profile_out(user.profile, user.username)


@router.put("/profile/me", response_model=ProfileOut)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    for key, value in payload.model_dump().items():
        setattr(user.profile, key, value)
    db.commit()
    db.refresh(user.profile)
    return _profile_out(user.profile, user.username)


@router.post("/profile/photo", response_model=ProfileOut)
async def upload_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Please upload an image smaller than 5 MB.")
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "photo.jpg").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        suffix = ".jpg"
    name = f"user-{user.id}{suffix}"
    dest = settings.upload_dir / name
    dest.write_bytes(contents)
    user.profile.photo_path = name
    db.commit()
    return _profile_out(user.profile, user.username)


@router.get("/u/{username}", response_model=PublicProfile)
def public_profile(
    username: str,
    db: Session = Depends(get_db),
    viewer: User | None = Depends(get_optional_user),
):
    user = db.query(User).filter(User.username == username.lower()).first()
    if not user or not user.profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    if not user.profile.is_public and (not viewer or viewer.id != user.id):
        raise HTTPException(status_code=403, detail="This profile is private.")
    return _public_profile(db, user, viewer)


@router.get("/s/{token}", response_model=PublicProfile)
def shared_profile(
    token: str,
    db: Session = Depends(get_db),
    viewer: User | None = Depends(get_optional_user),
):
    profile = db.query(Profile).filter(Profile.share_token == token).first()
    if not profile or not profile.user:
        raise HTTPException(status_code=404, detail="Share link is invalid.")
    if not profile.is_public and (not viewer or viewer.id != profile.user_id):
        raise HTTPException(status_code=403, detail="This profile is private.")
    return _public_profile(db, profile.user, viewer)


@router.post("/profile/share-token", response_model=ProfileOut)
def rotate_share_token(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user.profile.share_token = token_urlsafe(16)
    db.commit()
    db.refresh(user.profile)
    return _profile_out(user.profile, user.username)


def _crud(model, schema_in, schema_out, rel_name):
    list_router = APIRouter()

    @list_router.get("", response_model=list[schema_out])
    def list_items(user: User = Depends(get_current_user)):
        return getattr(user, rel_name)

    @list_router.post("", response_model=schema_out, status_code=201)
    def create_item(
        payload: schema_in,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ):
        item = model(user_id=user.id, **payload.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @list_router.put("/{item_id}", response_model=schema_out)
    def update_item(
        item_id: int,
        payload: schema_in,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ):
        item = db.get(model, item_id)
        if not item or item.user_id != user.id:
            raise HTTPException(status_code=404, detail="Item not found.")
        for key, value in payload.model_dump().items():
            setattr(item, key, value)
        db.commit()
        db.refresh(item)
        return item

    @list_router.delete("/{item_id}", status_code=204)
    def delete_item(
        item_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ):
        item = db.get(model, item_id)
        if not item or item.user_id != user.id:
            raise HTTPException(status_code=404, detail="Item not found.")
        db.delete(item)
        db.commit()

    return list_router


router.include_router(_crud(Experience, ExperienceIn, ExperienceOut, "experiences"), prefix="/experience")
router.include_router(_crud(Education, EducationIn, EducationOut, "education"), prefix="/education")
router.include_router(_crud(Skill, SkillIn, SkillOut, "skills"), prefix="/skills")
router.include_router(_crud(Language, LanguageIn, LanguageOut, "languages"), prefix="/languages")
