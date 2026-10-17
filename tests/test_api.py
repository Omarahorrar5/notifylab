import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db

engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                       poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False)

def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

def auth(username="sara", password="secret123"):
    client.post("/register", json={"username": username, "password": password})
    r = client.post("/login", data={"username": username, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def test_create_and_get_notification():
    h = auth()
    r = client.post("/notifications", headers=h,
                    json={"recipient": "bob@mail.com", "message": "Salut"})
    assert r.status_code == 201
    assert r.json()["status"] == "pending"
    r2 = client.get(f"/notifications/{r.json()['id']}", headers=h)
    assert r2.status_code == 200

def test_requires_authentication():
    assert client.get("/notifications/1").status_code == 401

def test_wrong_password():
    auth()
    r = client.post("/login", data={"username": "sara", "password": "mauvais"})
    assert r.status_code == 401

def test_duplicate_user():
    auth()
    r = client.post("/register", json={"username": "sara", "password": "secret123"})
    assert r.status_code == 409

def test_invalid_payload():
    r = client.post("/notifications", headers=auth(),
                    json={"recipient": "", "message": ""})
    assert r.status_code == 422

def test_not_found():
    assert client.get("/notifications/999", headers=auth()).status_code == 404

def test_cannot_read_other_users_notification():
    h1 = auth("sara")
    notif_id = client.post("/notifications", headers=h1,
                           json={"recipient": "x", "message": "y"}).json()["id"]
    h2 = auth("karim")
    assert client.get(f"/notifications/{notif_id}", headers=h2).status_code == 403