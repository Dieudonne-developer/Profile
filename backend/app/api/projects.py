from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user
from app.models import Comment, Project, ProjectLike, User
from app.schemas import CommentIn, CommentOut, ProjectIn, ProjectOut
from app.services.notify import notify
from app.services.profile import project_out

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def list_mine(user: User = Depends(get_current_user)):
    return [project_out(project, user.id) for project in user.projects]


@router.get("/feed", response_model=list[ProjectOut])
def feed(
    db: Session = Depends(get_db),
    viewer: User | None = Depends(get_optional_user),
):
    rows = (
        db.query(Project)
        .options(joinedload(Project.likes), joinedload(Project.comments), joinedload(Project.user))
        .order_by(Project.created_at.desc())
        .limit(40)
        .all()
    )
    current_id = viewer.id if viewer else None
    return [project_out(project, current_id) for project in rows]


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    payload: ProjectIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = Project(user_id=user.id, **payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project_out(project, user.id)


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    payload: ProjectIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = db.get(Project, project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found.")
    for key, value in payload.model_dump().items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project_out(project, user.id)


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = db.get(Project, project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found.")
    db.delete(project)
    db.commit()


@router.post("/{project_id}/like", response_model=ProjectOut)
def toggle_like(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    existing = (
        db.query(ProjectLike)
        .filter(ProjectLike.user_id == user.id, ProjectLike.project_id == project_id)
        .first()
    )
    if existing:
        db.delete(existing)
    else:
        db.add(ProjectLike(user_id=user.id, project_id=project_id))
        if project.user_id != user.id:
            notify(
                db,
                project.user_id,
                "like",
                f"{user.username} liked your project",
                project.title,
                f"/u/{project.user.username}",
            )
    db.commit()
    db.refresh(project)
    return project_out(project, user.id)


@router.get("/{project_id}/comments", response_model=list[CommentOut])
def list_comments(project_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(Comment)
        .options(joinedload(Comment.user))
        .filter(Comment.project_id == project_id)
        .order_by(Comment.created_at.asc())
        .all()
    )
    return [
        CommentOut(
            id=row.id,
            user_id=row.user_id,
            project_id=row.project_id,
            body=row.body,
            author=row.user.username,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.post("/{project_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(
    project_id: int,
    payload: CommentIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    comment = Comment(user_id=user.id, project_id=project_id, body=payload.body.strip())
    db.add(comment)
    if project.user_id != user.id:
        notify(
            db,
            project.user_id,
            "comment",
            f"{user.username} commented on {project.title}",
            payload.body[:180],
            f"/u/{project.user.username}",
        )
    db.commit()
    db.refresh(comment)
    return CommentOut(
        id=comment.id,
        user_id=comment.user_id,
        project_id=comment.project_id,
        body=comment.body,
        author=user.username,
        created_at=comment.created_at,
    )
