"""
StudyMate API - Day 5
Topics: JWT authentication and task queues (background tasks)
Run:  uvicorn main:app --reload
NOTE: the tables changed today -> delete the old studymate.db before starting.
"""

import os
import asyncio
import re
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import col, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from auth import create_access_token, get_current_user, hash_password, verify_password
from database import engine, get_session, init_db
from models import (ImportRequest, Note, NoteCreate, NoteRead, NoteUpdate, Token, User,
                    UserCreate, UserRead)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


#app = FastAPI(title="StudyMate API", version="0.3", lifespan=lifespan)
app = FastAPI(title="StudyMate API", version="0.4", lifespan=lifespan)

# ---------------------------------------------------------------
# NEW: CORS - allow the browser app on another origin (port 5173) to call us
# ---------------------------------------------------------------
ALLOWED_ORIGINS = os.getenv("FRONTEND_URL", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def home():
    return {"app": "StudyMate", "status": "running on CI|CD"}


# ---------------------------------------------------------------
# NEW: Auth endpoints
# ---------------------------------------------------------------
@app.post("/auth/signup", response_model=UserRead, status_code=201)
async def signup(data: UserCreate, session: AsyncSession = Depends(get_session)):
    existing = await session.exec(select(User).where(User.email == data.email.lower()))
    if existing.first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=data.email.lower(), hashed_password=hash_password(data.password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@app.post("/auth/login", response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends(),
                session: AsyncSession = Depends(get_session)):
    # OAuth2 form uses the field name "username" - we put the email in it
    result = await session.exec(select(User).where(User.email == form.username.lower()))
    user = result.first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Wrong email or password")
    return Token(access_token=create_access_token(user.id))


@app.get("/auth/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)):
    return user


# ---------------------------------------------------------------
# NEW: Background task -> runs AFTER the response is sent
# ---------------------------------------------------------------
async def count_words(note_id: int):
    await asyncio.sleep(2)  # pretend this is slow work (e.g. AI processing)
    async with AsyncSession(engine) as session:
        note = await session.get(Note, note_id)
        if note:
            words = len(note.content.split())
            note.word_count = words
            session.add(note)
            await session.commit()
            print(f"[background] note {note_id}: {words} words")


# ---------------------------------------------------------------
# Notes - now protected: every endpoint needs a logged-in user
# and only sees that user's notes
# ---------------------------------------------------------------
@app.post("/notes", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
async def create_note(data: NoteCreate, background: BackgroundTasks,
                      user: User = Depends(get_current_user),
                      session: AsyncSession = Depends(get_session)):
    note = Note.model_validate(data, update={"owner_id": user.id})
    session.add(note)
    await session.commit()
    await session.refresh(note)
    background.add_task(count_words, note.id)
    return note


@app.get("/notes", response_model=list[NoteRead])
async def list_notes(subject: str | None = None, q: str | None = None,
                     user: User = Depends(get_current_user),
                     session: AsyncSession = Depends(get_session)):
    query = select(Note).where(Note.owner_id == user.id).order_by(col(Note.created_at).desc())
    if subject:
        query = query.where(Note.subject == subject)
    if q:
        query = query.where(or_(col(Note.title).contains(q), col(Note.content).contains(q)))
    result = await session.exec(query)
    return result.all()


async def get_own_note(note_id: int, user: User, session: AsyncSession) -> Note:
    note = await session.get(Note, note_id)
    if not note or note.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.get("/notes/{note_id}", response_model=NoteRead)
async def get_note(note_id: int, user: User = Depends(get_current_user),
                   session: AsyncSession = Depends(get_session)):
    return await get_own_note(note_id, user, session)


@app.put("/notes/{note_id}", response_model=NoteRead)
async def update_note(note_id: int, data: NoteUpdate, background: BackgroundTasks,
                      user: User = Depends(get_current_user),
                      session: AsyncSession = Depends(get_session)):
    note = await get_own_note(note_id, user, session)
    note.sqlmodel_update(data.model_dump(exclude_unset=True))
    session.add(note)
    await session.commit()
    await session.refresh(note)
    background.add_task(count_words, note.id)
    return note


@app.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(note_id: int, user: User = Depends(get_current_user),
                      session: AsyncSession = Depends(get_session)):
    note = await get_own_note(note_id, user, session)
    await session.delete(note)
    await session.commit()


# ---------------- Import from web pages (from Day 4) ----------------
def html_to_text(html: str) -> str:
    text = re.sub(r"<(script|style).*?</\1>", " ", html, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


async def fetch_page(client: httpx.AsyncClient, url: str) -> tuple[str, str]:
    response = await client.get(url, follow_redirects=True)
    return url, html_to_text(response.text)[:2000]


@app.post("/notes/import", response_model=list[NoteRead], status_code=201)
async def import_notes(data: ImportRequest, background: BackgroundTasks,
                       user: User = Depends(get_current_user),
                       session: AsyncSession = Depends(get_session)):
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=15) as client:
        results = await asyncio.gather(*(fetch_page(client, u) for u in data.urls),
                                       return_exceptions=True)
    print(f"Fetched {len(data.urls)} pages in {time.perf_counter() - start:.2f}s")

    created = []
    for item in results:
        if isinstance(item, Exception):
            continue
        url, text = item
        note = Note(title=url[:100], content=text or "(empty page)",
                    subject=data.subject, owner_id=user.id)
        session.add(note)
        created.append(note)
    await session.commit()
    for note in created:
        await session.refresh(note)
        background.add_task(count_words, note.id)
    return created