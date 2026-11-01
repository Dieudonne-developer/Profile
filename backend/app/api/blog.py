from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import BlogPost, User
from app.schemas import BlogPostIn, BlogPostOut

router = APIRouter(prefix="/posts", tags=["blog"])


@router.get("", response_model=list[BlogPostOut])
def list_mine(user: User = Depends(get_current_user)):
    return sorted(user.posts, key=lambda item: (item.sort_order, item.id))


@router.post("", response_model=BlogPostOut, status_code=201)
def create_post(
    payload: BlogPostIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    post = BlogPost(user_id=user.id, **payload.model_dump())
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.put("/{post_id}", response_model=BlogPostOut)
def update_post(
    post_id: int,
    payload: BlogPostIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    post = db.get(BlogPost, post_id)
    if not post or post.user_id != user.id:
        raise HTTPException(status_code=404, detail="Post not found.")
    for key, value in payload.model_dump().items():
        setattr(post, key, value)
    db.commit()
    db.refresh(post)
    return post


@router.delete("/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    post = db.get(BlogPost, post_id)
    if not post or post.user_id != user.id:
        raise HTTPException(status_code=404, detail="Post not found.")
    db.delete(post)
    db.commit()
