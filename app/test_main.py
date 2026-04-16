from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "SentinelCI is running"}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_get_user():
    response = client.get("/users/7")
    assert response.status_code == 200
    assert response.json() == {"user_id": 7, "name": "test_user"}
