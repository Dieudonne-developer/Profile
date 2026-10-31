from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user
from app.models import AnalyticsEvent, User
from app.services.cv import build_cv_pdf
from app.services.profile import public_bundle

router = APIRouter(prefix="/cv", tags=["cv"])


def _bundle_dict(bundle: dict) -> dict:
    profile = bundle["profile"]
    photo = ""
    if profile.photo_path:
        candidate = get_settings().upload_dir / profile.photo_path
        if candidate.exists():
            photo = str(candidate)
    return {
        "user": {"username": bundle["user"].username, "email": bundle["user"].email},
        "photo_path": photo,
        "profile": {
            "full_name": profile.full_name,
            "headline": profile.headline,
            "bio": profile.bio,
            "location": profile.location,
            "phone": profile.phone,
            "public_email": profile.public_email,
            "website": profile.website,
            "github": profile.github,
            "linkedin": profile.linkedin,
            "twitter": profile.twitter,
            "birthday": getattr(profile, "birthday", "") or "",
        },
        "experiences": [
            {
                "title": item.title,
                "company": item.company,
                "start_date": item.start_date,
                "end_date": item.end_date,
                "is_current": item.is_current,
                "description": item.description,
            }
            for item in bundle["experiences"]
        ],
        "education": [
            {
                "institution": item.institution,
                "degree": item.degree,
                "start_date": item.start_date,
                "end_date": item.end_date,
                "description": item.description,
            }
            for item in bundle["education"]
        ],
        "skills": [{"name": item.name, "category": item.category} for item in bundle["skills"]],
        "languages": [
            {"name": item.name, "proficiency": item.proficiency}
            for item in bundle["languages"]
        ],
        "projects": [
            {
                "title": item.title,
                "summary": item.summary,
                "description": item.description,
                "repo_url": item.repo_url,
            }
            for item in bundle["projects"]
        ],
    }


@router.get("/me")
def download_mine(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    pdf = build_cv_pdf(_bundle_dict(public_bundle(db, user, user)))
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{user.username}-cv.pdf"'},
    )


@router.get("/{username}")
def download_public(
    username: str,
    db: Session = Depends(get_db),
    viewer: User | None = Depends(get_optional_user),
):
    user = db.query(User).filter(User.username == username.lower()).first()
    if not user or not user.profile or not user.profile.is_public:
        raise HTTPException(status_code=404, detail="CV is not available.")
    db.add(
        AnalyticsEvent(
            owner_id=user.id,
            event_type="cv_download",
            visitor_hash=str(viewer.id if viewer else "anon"),
            path=f"/cv/{username}",
            meta={},
        )
    )
    db.commit()
    pdf = build_cv_pdf(_bundle_dict(public_bundle(db, user, viewer)))
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{user.username}-cv.pdf"'},
    )
