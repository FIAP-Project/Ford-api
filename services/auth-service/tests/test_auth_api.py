"""HTTP integration tests for auth-service endpoints.

Covers success, validation-error, conflict and unauthorized scenarios for
register/login/refresh/me, plus the public health check.
"""

from __future__ import annotations

VALID_PASSWORD = "Strong#Pass123!"


def test_health_is_public(client):
    response = client.get("/auth/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_success(client):
    response = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": VALID_PASSWORD, "full_name": "John Doe"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "user@example.com"
    assert body["role"] == "user"
    assert body["full_name"] == "John Doe"
    assert "id" in body


def test_register_duplicate_email_returns_409(client):
    payload = {"email": "dup@example.com", "password": VALID_PASSWORD}
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/register", json=payload)

    assert second.status_code == 409
    assert second.json()["error"]["message"] == "Email already registered"


def test_register_weak_password_returns_422(client):
    response = client.post(
        "/auth/register",
        json={"email": "weak@example.com", "password": "short"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == 422


def test_register_rejects_unknown_fields(client):
    response = client.post(
        "/auth/register",
        json={"email": "extra@example.com", "password": VALID_PASSWORD, "is_admin": True},
    )

    assert response.status_code == 422


def test_login_success_returns_token_pair(client):
    client.post(
        "/auth/register", json={"email": "login@example.com", "password": VALID_PASSWORD}
    )

    response = client.post(
        "/auth/login", json={"email": "login@example.com", "password": VALID_PASSWORD}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "Bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["expires_in"] == 15 * 60


def test_login_wrong_password_returns_401(client):
    client.post(
        "/auth/register", json={"email": "wrongpw@example.com", "password": VALID_PASSWORD}
    )

    response = client.post(
        "/auth/login", json={"email": "wrongpw@example.com", "password": "totally-wrong"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid email or password"


def test_login_unknown_email_returns_401(client):
    response = client.post(
        "/auth/login", json={"email": "ghost@example.com", "password": VALID_PASSWORD}
    )

    assert response.status_code == 401


def test_refresh_rotates_tokens(client):
    client.post(
        "/auth/register", json={"email": "refresh@example.com", "password": VALID_PASSWORD}
    )
    login = client.post(
        "/auth/login", json={"email": "refresh@example.com", "password": VALID_PASSWORD}
    ).json()

    response = client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]})

    assert response.status_code == 200
    rotated = response.json()
    assert rotated["access_token"] != login["access_token"]
    assert rotated["refresh_token"] != login["refresh_token"]


def test_refresh_with_revoked_token_returns_401(client):
    client.post(
        "/auth/register", json={"email": "revoke@example.com", "password": VALID_PASSWORD}
    )
    login = client.post(
        "/auth/login", json={"email": "revoke@example.com", "password": VALID_PASSWORD}
    ).json()
    client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]})

    # Reusing the same (now rotated/revoked) refresh token must fail.
    response = client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]})

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Refresh token revoked or unknown"


def test_refresh_with_garbage_token_returns_401(client):
    response = client.post("/auth/refresh", json={"refresh_token": "not-a-real-jwt-token"})

    assert response.status_code == 401


def test_me_without_token_returns_401(client):
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Missing or invalid Authorization header"


def test_me_with_valid_token_returns_profile(client):
    client.post(
        "/auth/register", json={"email": "me@example.com", "password": VALID_PASSWORD}
    )
    login = client.post(
        "/auth/login", json={"email": "me@example.com", "password": VALID_PASSWORD}
    ).json()

    response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {login['access_token']}"}
    )

    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


def test_me_with_malformed_token_returns_401(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-jwt"})

    assert response.status_code == 401
