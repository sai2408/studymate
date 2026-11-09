import os
import sys
from pathlib import Path

# Use a separate test database, and make the backend folder importable
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_studymate.db"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    Path("test_studymate.db").unlink(missing_ok=True)
    from main import app
    from database import engine
    with TestClient(app) as c:
        yield c
        c.portal.call(engine.dispose)   # close DB connections first (Windows can't delete an open file)
    Path("test_studymate.db").unlink(missing_ok=True)


@pytest.fixture(scope="session")
def auth_headers(client):
    client.post("/auth/signup", json={"email": "test@example.com", "password": "secret123"})
    r = client.post("/auth/login", data={"username": "test@example.com", "password": "secret123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}