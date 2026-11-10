import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.security import hash_password, new_device_key


@pytest.fixture
def client():
    settings = Settings(storage="memory", jwt_secret="test-secret", supabase_url="", supabase_key="")
    app = create_app(settings)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def storage(client):
    return client.app.state.storage


@pytest.fixture
def device_key(storage):
    key, key_hash = new_device_key()
    storage.insert_device({"device_name": "cam-north", "location": "North paddock", "status": "Active",
                           "api_key_hash": key_hash})
    return key


@pytest.fixture
def admin_token(client, storage):
    storage.insert_user({"username": "admin", "password_hash": hash_password("adminpass123"), "role": "admin"})
    r = client.post("/auth/login", data={"username": "admin", "password": "adminpass123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
def auth(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
