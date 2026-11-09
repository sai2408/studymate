def test_home(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["app"] == "StudyMate"


def test_notes_need_login(client):
    assert client.get("/notes").status_code == 401


def test_wrong_password(client, auth_headers):
    r = client.post("/auth/login", data={"username": "test@example.com", "password": "wrong"})
    assert r.status_code == 401


def test_create_list_update_delete(client, auth_headers):
    r = client.post("/notes", json={"title": "CI test", "content": "pipelines run tests"}, headers=auth_headers)
    assert r.status_code == 201
    note_id = r.json()["id"]

    titles = [n["title"] for n in client.get("/notes", headers=auth_headers).json()]
    assert "CI test" in titles

    r = client.put(f"/notes/{note_id}", json={"subject": "DevOps"}, headers=auth_headers)
    assert r.json()["subject"] == "DevOps"

    assert client.delete(f"/notes/{note_id}", headers=auth_headers).status_code == 204
    assert client.get(f"/notes/{note_id}", headers=auth_headers).status_code == 404


def test_validation_error(client, auth_headers):
    r = client.post("/notes", json={"title": "", "content": "x"}, headers=auth_headers)
    assert r.status_code == 422