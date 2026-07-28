"""Integration tests — Authentication API endpoints"""

import pytest


BASE = "/api/v1/auth"

VALID_REGISTER = {
    "email":      "newuser@test.com",
    "username":   "newuser99",
    "password":   "SecurePass@1",
    "first_name": "New",
    "last_name":  "User",
    "role":       "citizen",
}


class TestRegister:
    def test_successful_registration(self, client):
        resp = client.post(f"{BASE}/register", json=VALID_REGISTER)
        assert resp.status_code == 201
        data = resp.get_json()
        assert "user" in data
        assert data["user"]["email"] == "newuser@test.com"

    def test_duplicate_email(self, client):
        client.post(f"{BASE}/register", json=VALID_REGISTER)
        resp = client.post(f"{BASE}/register", json=VALID_REGISTER)
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_missing_email(self, client):
        payload = {**VALID_REGISTER, "email": ""}
        resp = client.post(f"{BASE}/register", json=payload)
        assert resp.status_code == 400

    def test_weak_password(self, client):
        payload = {**VALID_REGISTER, "email": "weak@test.com",
                   "username": "weakuser", "password": "weakpassword"}
        resp = client.post(f"{BASE}/register", json=payload)
        assert resp.status_code == 400

    def test_invalid_email_format(self, client):
        payload = {**VALID_REGISTER, "email": "not-an-email", "username": "invuser2"}
        resp = client.post(f"{BASE}/register", json=payload)
        assert resp.status_code == 400

    def test_role_defaulted_to_citizen(self, client):
        payload = {**VALID_REGISTER, "email": "r2@test.com", "username": "ruser2", "role": "admin"}
        resp = client.post(f"{BASE}/register", json=payload)
        assert resp.status_code == 201
        assert resp.get_json()["user"]["role"] == "citizen"


class TestLogin:
    @pytest.fixture(autouse=True)
    def _register(self, client):
        client.post(f"{BASE}/register", json={**VALID_REGISTER,
            "email": "login@test.com", "username": "logintest"})

    def test_successful_login(self, client):
        resp = client.post(f"{BASE}/login",
                           json={"email": "login@test.com", "password": "SecurePass@1"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data

    def test_wrong_password(self, client):
        resp = client.post(f"{BASE}/login",
                           json={"email": "login@test.com", "password": "WrongPass@99"})
        assert resp.status_code == 401

    def test_unknown_email(self, client):
        resp = client.post(f"{BASE}/login",
                           json={"email": "nobody@test.com", "password": "Pass@1234"})
        assert resp.status_code == 401

    def test_missing_fields(self, client):
        resp = client.post(f"{BASE}/login", json={"email": "login@test.com"})
        assert resp.status_code == 400


class TestProtectedRoutes:
    def test_get_me_without_token(self, client):
        resp = client.get(f"{BASE}/me")
        assert resp.status_code == 401

    def test_get_me_with_token(self, client, citizen_token):
        resp = client.get(f"{BASE}/me",
                          headers={"Authorization": f"Bearer {citizen_token}"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "user" in data

    def test_update_profile(self, client, citizen_token):
        resp = client.put(f"{BASE}/me",
                          json={"first_name": "Updated"},
                          headers={"Authorization": f"Bearer {citizen_token}"})
        assert resp.status_code == 200
        assert resp.get_json()["user"]["first_name"] == "Updated"

    def test_invalid_token(self, client):
        resp = client.get(f"{BASE}/me",
                          headers={"Authorization": "Bearer invalid.token.here"})
        assert resp.status_code == 401


class TestForgotResetPassword:
    def test_forgot_password_always_200(self, client):
        # Should return 200 even for non-existent email (prevent enumeration)
        resp = client.post(f"{BASE}/forgot-password",
                           json={"email": "nobody@test.com"})
        assert resp.status_code == 200

    def test_reset_with_invalid_token(self, client):
        resp = client.post(f"{BASE}/reset-password",
                           json={"token": "invalid_token", "new_password": "NewPass@99"})
        assert resp.status_code == 400

    def test_reset_weak_password(self, client):
        resp = client.post(f"{BASE}/reset-password",
                           json={"token": "any_token", "new_password": "weak"})
        assert resp.status_code == 400
