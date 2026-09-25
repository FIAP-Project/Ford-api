"""HTTP integration tests for user-service endpoints.

Covers success, not-found, unauthorized (401) and forbidden (403 — RBAC)
scenarios across /users/me, /users and /users/{id}/role.
"""

from __future__ import annotations

from ford_shared.security.rbac import Role


def test_health_is_public(client):
    response = client.get("/users/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_me_without_token_returns_401(client):
    response = client.get("/users/me")

    assert response.status_code == 401


def test_me_without_profile_returns_404(client, make_token):
    _, headers = make_token()

    response = client.get("/users/me", headers=headers)

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Profile not found"


async def test_me_returns_seeded_profile(client, profile_repo, make_token):
    user_id, headers = make_token(email="jane@example.com", role=Role.USER)
    await profile_repo.upsert_from_event(
        auth_user_id=user_id, email="jane@example.com", role="user", full_name="Jane"
    )

    response = client.get("/users/me", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "jane@example.com"
    assert body["full_name"] == "Jane"


async def test_update_me_changes_full_name(client, profile_repo, make_token):
    user_id, headers = make_token(email="patch@example.com")
    await profile_repo.upsert_from_event(
        auth_user_id=user_id, email="patch@example.com", role="user", full_name=None
    )

    response = client.patch("/users/me", json={"full_name": "New Name"}, headers=headers)

    assert response.status_code == 200
    assert response.json()["full_name"] == "New Name"


def test_update_me_rejects_unknown_fields(client, make_token):
    _, headers = make_token()

    response = client.patch("/users/me", json={"role": "admin"}, headers=headers)

    assert response.status_code == 422


def test_list_profiles_requires_analyst_role(client, make_token):
    _, headers = make_token(role=Role.USER)

    response = client.get("/users", headers=headers)

    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Insufficient privileges"


def test_list_profiles_allows_analyst_role(client, make_token):
    _, headers = make_token(role=Role.ANALYST)

    response = client.get("/users", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


def test_list_profiles_without_token_returns_401(client):
    response = client.get("/users")

    assert response.status_code == 401


def test_update_role_requires_admin_role(client, make_token):
    _, admin_headers = make_token(role=Role.ANALYST)
    target_id, _ = make_token(role=Role.USER)

    response = client.put(
        f"/users/{target_id}/role", json={"role": "admin"}, headers=admin_headers
    )

    assert response.status_code == 403


async def test_update_role_as_admin_succeeds(client, profile_repo, make_token):
    target_id, _ = make_token(email="target@example.com")
    await profile_repo.upsert_from_event(
        auth_user_id=target_id, email="target@example.com", role="user", full_name=None
    )
    _, admin_headers = make_token(role=Role.ADMIN)

    response = client.put(
        f"/users/{target_id}/role", json={"role": "analyst"}, headers=admin_headers
    )

    assert response.status_code == 200
    assert response.json()["role"] == "analyst"


def test_update_role_for_unknown_user_returns_404(client, make_token):
    _, admin_headers = make_token(role=Role.ADMIN)
    from uuid import uuid4

    response = client.put(
        f"/users/{uuid4()}/role", json={"role": "admin"}, headers=admin_headers
    )

    assert response.status_code == 404


def test_update_role_rejects_invalid_role_value(client, make_token):
    target_id, _ = make_token()
    _, admin_headers = make_token(role=Role.ADMIN)

    response = client.put(
        f"/users/{target_id}/role", json={"role": "superadmin"}, headers=admin_headers
    )

    assert response.status_code == 422
