from sqlalchemy.orm import Session

from app.models import Follow, Project, User
from app.schemas import ProjectOut


def photo_url(path: str) -> str:
    if not path:
        return ""
    if path.startswith("http"):
        return path
    return f"/media/{path.lstrip('/')}"


def project_out(project: Project, current_id: int | None = None) -> ProjectOut:
    return ProjectOut(
        id=project.id,
        user_id=project.user_id,
        title=project.title,
        summary=project.summary,
        description=project.description,
        tags=project.tags or [],
        repo_url=project.repo_url,
        live_url=project.live_url,
        image_url=project.image_url,
        featured=project.featured,
        sort_order=project.sort_order,
        likes=len(project.likes),
        comments=len(project.comments),
        liked=any(like.user_id == current_id for like in project.likes)
        if current_id
        else False,
        author=project.user.username if project.user else None,
        created_at=project.created_at,
    )


def follow_counts(db: Session, user_id: int) -> tuple[int, int]:
    followers = db.query(Follow).filter(Follow.following_id == user_id).count()
    following = db.query(Follow).filter(Follow.follower_id == user_id).count()
    return followers, following


def public_bundle(db: Session, user: User, viewer: User | None = None) -> dict:
    profile = user.profile
    followers, following = follow_counts(db, user.id)
    is_following = False
    if viewer:
        is_following = (
            db.query(Follow)
            .filter(Follow.follower_id == viewer.id, Follow.following_id == user.id)
            .first()
            is not None
        )
    return {
        "user": user,
        "profile": profile,
        "experiences": sorted(user.experiences, key=lambda item: item.sort_order),
        "education": sorted(user.education, key=lambda item: item.sort_order),
        "skills": user.skills,
        "languages": user.languages,
        "projects": [
            project_out(project, viewer.id if viewer else None)
            for project in sorted(user.projects, key=lambda item: item.sort_order)
        ],
        "followers": followers,
        "following": following,
        "is_following": is_following,
    }
