from secrets import token_urlsafe

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Profile, User
from app.schemas import LoginRequest, Token, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if not get_settings().allow_registration:
        raise HTTPException(
            status_code=403,
            detail="This is a personal portfolio. New accounts cannot be created.",
        )
    username = payload.username.strip().lower()
    email = payload.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with that email already exists.")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=409, detail="That username is taken.")
    user = User(
        email=email,
        username=username,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.flush()
    db.add(
        Profile(
            user_id=user.id,
            full_name=payload.full_name or username.title(),
            birthday="2002-01-01",
            share_token=token_urlsafe(16),
            is_public=True,
        )
    )
    db.commit()
    return Token(access_token=create_access_token(str(user.id)))


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    ident = payload.email.strip().lower()
    user = db.query(User).filter(User.email == ident).first()
    if not user:
        user = db.query(User).filter(User.username == ident).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return Token(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
