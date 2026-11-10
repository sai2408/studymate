"""Tables and request/response models."""
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now():
    return datetime.now(timezone.utc)


# ---------------- Users ----------------
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
    owner_id: int = Field(foreign_key="user.id", index=True)
    word_count: int = 0


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


# ---------------- RAG (NEW today) ----------------
class NoteChunk(SQLModel, table=True):
    """A piece of a note plus its embedding (stored as a JSON list of numbers)."""
    id: int | None = Field(default=None, primary_key=True)
    note_id: int = Field(foreign_key="note.id", index=True)
    owner_id: int = Field(index=True)
    text: str
    embedding: str


class AskRequest(SQLModel):
    question: str = Field(min_length=3, max_length=500)


class Source(SQLModel):
    note_id: int
    title: str


class AskResponse(SQLModel):
    answer: str
    sources: list[Source]



# ---------------- Agent (NEW today) ----------------
class ChatMessage(SQLModel):
    role: str            # "user" or "assistant"
    content: str


class BuddyRequest(SQLModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatMessage] = []


class AgentStep(SQLModel):
    tool: str
    args: dict
    result: str


class BuddyResponse(SQLModel):
    reply: str
    steps: list[AgentStep]