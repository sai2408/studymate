"""Tables and request/response models."""
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now():
    return datetime.now(timezone.utc)


# ---------------- Users (NEW today) ----------------
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=utc_now)


class UserCreate(SQLModel):
    email: str = Field(min_length=5, max_length=100)
    password: str = Field(min_length=6, max_length=50)


class UserRead(SQLModel):
    id: int
    email: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# ---------------- Notes ----------------
class NoteBase(SQLModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    subject: str = "General"


class Note(NoteBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)
    owner_id: int = Field(foreign_key="user.id", index=True)   # NEW: who owns the note
    word_count: int = 0                                        # NEW: filled by a background task


class NoteCreate(NoteBase):
    pass


class NoteRead(NoteBase):
    id: int
    created_at: datetime
    word_count: int


class NoteUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1)
    subject: str | None = None


class ImportRequest(SQLModel):
    urls: list[str]
    subject: str = "Web"