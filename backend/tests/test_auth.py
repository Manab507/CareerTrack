import pytest
from fastapi.testclient import TestClient
from app.main import app

# TestClient toiri koro (ETA API ke hit korbe)
client = TestClient(app)

def test_root_endpoint():
    """Test 1: Root endpoint thik ache ki na"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to CareerTrack API 🚀"}

def test_login_invalid_user():
    """Test 2: Vul email/password diye login korle 401 asha uchit"""
    response = client.post(
        "/login",  # Tomar router prefix onujayi (jemon /login ba /auth/login)
        json={"email": "wrong@example.com", "password": "wrongpass"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

def test_login_success():
    """Test 3: Thik email/password diye login korle 200 + Token asha uchit"""
    response = client.post(
        "/login",
        json={"email": "oxforduniversity100@gmail.com", "password": "Manab507@"} # Tomar asol account
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data