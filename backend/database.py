"""Database connection (async SQLite via SQLModel + aiosqlite)."""
import os

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./studymate.db")

engine = create_async_engine(DATABASE_URL, echo=False)


async def init_db():
    """Create all tables that don't exist yet."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session():
    """FastAPI dependency: one session per request."""
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session