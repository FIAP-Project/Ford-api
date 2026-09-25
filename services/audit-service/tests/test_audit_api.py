"""HTTP integration tests for audit-service endpoints.

Covers admin-only access control (401/403), successful listing, and
filtering by event_type/actor_user_id on GET /audit/events.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ford_shared.security.rbac import Role


async def _seed(event_repo, *, event_type="vehicle.query.completed", actor_user_id=None):
    return await event_repo.append(
        event_type=event_type,
        routing_key=event_type,
        actor_user_id=actor_user_id,
        payload={"foo": "bar"},
        occurred_at=datetime.now(UTC),
        signature="deadbeef",
    )


def test_health_is_public(client):
    response = client.get("/audit/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_events_without_token_returns_401(client):
    response = client.get("/audit/events")

    assert response.status_code == 401


def test_list_events_requires_admin_role(client, make_token):
    _, headers = make_token(role=Role.ANALYST)

    response = client.get("/audit/events", headers=headers)

    assert response.status_code == 403


async def test_list_events_as_admin_returns_seeded_events(client, event_repo, make_token):
    await _seed(event_repo)
    await _seed(event_repo)
    _, headers = make_token(role=Role.ADMIN)

    response = client.get("/audit/events", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_list_events_filters_by_event_type(client, event_repo, make_token):
    await _seed(event_repo, event_type="vehicle.query.completed")
    await _seed(event_repo, event_type="user.registered")
    _, headers = make_token(role=Role.ADMIN)

    response = client.get(
        "/audit/events", params={"event_type": "user.registered"}, headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["event_type"] == "user.registered"


async def test_list_events_filters_by_actor_user_id(client, event_repo, make_token):
    from uuid import uuid4

    actor_id = uuid4()
    await _seed(event_repo, actor_user_id=actor_id)
    await _seed(event_repo, actor_user_id=uuid4())
    _, headers = make_token(role=Role.ADMIN)

    response = client.get(
        "/audit/events", params={"actor_user_id": str(actor_id)}, headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["actor_user_id"] == str(actor_id)
