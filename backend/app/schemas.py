from datetime import datetime
from typing import Annotated

from email_validator import EmailNotValidError, validate_email
from pydantic import AfterValidator, BaseModel, Field


def _normalize_email(value: str) -> str:
    text = str(value).strip()
    try:
        return validate_email(text, check_deliverability=False).normalized
    except EmailNotValidError as exc:
        message = str(exc).lower()
        if "special-use" in message or "reserved name" in message:
            local, _, domain = text.partition("@")
            if local and domain and "." in domain:
                return text.lower()
        raise ValueError("Enter a valid email address.") from exc


AppEmail = Annotated[str, AfterValidator(_normalize_email)]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: AppEmail
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=8, max_length=128)
    full_name: str = ""


class LoginRequest(BaseModel):
    email: AppEmail
    password: str


class UserOut(BaseModel):
    id: int
    email: AppEmail
    username: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileBase(BaseModel):
    full_name: str = ""
    headline: str = ""
    bio: str = ""
    location: str = ""
    phone: str = ""
    public_email: str = ""
    website: str = ""
    github: str = ""
    linkedin: str = ""
    twitter: str = ""
    birthday: str = "2002-01-01"
    is_public: bool = True


class ProfileUpdate(ProfileBase):
    pass


class ProfileOut(ProfileBase):
    id: int
    user_id: int
    photo_path: str = ""
    share_token: str
    username: str | None = None

    model_config = {"from_attributes": True}


class ExperienceIn(BaseModel):
    title: str
    company: str
    location: str = ""
    start_date: str = ""
    end_date: str | None = None
    is_current: bool = False
    description: str = ""
    sort_order: int = 0


class ExperienceOut(ExperienceIn):
    id: int
    user_id: int
    model_config = {"from_attributes": True}


class EducationIn(BaseModel):
    institution: str
    degree: str = ""
    field: str = ""
    start_date: str = ""
    end_date: str | None = None
    description: str = ""
    sort_order: int = 0


class EducationOut(EducationIn):
    id: int
    user_id: int
    model_config = {"from_attributes": True}


class SkillIn(BaseModel):
    name: str
    category: str = "General"
    level: int = Field(default=70, ge=0, le=100)


class SkillOut(SkillIn):
    id: int
    user_id: int
    model_config = {"from_attributes": True}


class LanguageIn(BaseModel):
    name: str
    proficiency: str = "Professional"


class LanguageOut(LanguageIn):
    id: int
    user_id: int
    model_config = {"from_attributes": True}


class ProjectIn(BaseModel):
    title: str
    summary: str = ""
    description: str = ""
    tags: list[str] = []
    repo_url: str = ""
    live_url: str = ""
    image_url: str = ""
    featured: bool = False
    sort_order: int = 0


class ProjectOut(ProjectIn):
    id: int
    user_id: int
    likes: int = 0
    comments: int = 0
    liked: bool = False
    author: str | None = None
    created_at: datetime | None = None
    model_config = {"from_attributes": True}


class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class CommentOut(BaseModel):
    id: int
    user_id: int
    project_id: int
    body: str
    author: str
    created_at: datetime
    model_config = {"from_attributes": True}


class NotificationOut(BaseModel):
    id: int
    type: str
    title: str
    body: str
    link: str
    is_read: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class NetworkUser(BaseModel):
    id: int
    username: str
    full_name: str
    headline: str
    photo_path: str
    followers: int
    following: int
    is_following: bool = False


class TrackIn(BaseModel):
    username: str
    event_type: str = "profile_view"
    path: str = ""
    referrer: str = ""


class AIImproveIn(BaseModel):
    kind: str = Field(pattern="^(bio|project)$")
    text: str = Field(min_length=8, max_length=8000)
    tone: str = "professional"


class AIImproveOut(BaseModel):
    original: str
    improved: str
    provider: str


class PublicProfile(BaseModel):
    user: UserOut
    profile: ProfileOut
    experiences: list[ExperienceOut]
    education: list[EducationOut]
    skills: list[SkillOut]
    languages: list[LanguageOut]
    projects: list[ProjectOut]
    followers: int
    following: int
    is_following: bool = False
