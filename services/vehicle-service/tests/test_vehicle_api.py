"""HTTP integration tests for vehicle-service endpoints.

Covers success, upstream-failure, unauthorized/forbidden and validation
scenarios across POST /vehicles/query, GET /vehicles/queries and
GET /vehicles/queries/{id}.
"""

from __future__ import annotations

from ford_shared.security.rbac import Role

VALID_PAYLOAD = {
    "brand": "Ford",
    "model": "Ranger",
    "version": "Raptor",
    "attributes": ["horsepower", "torque"],
}


def test_health_is_public(client):
    response = client.get("/vehicles/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_query_without_token_returns_401(client):
    response = client.post("/vehicles/query", json=VALID_PAYLOAD)

    assert response.status_code == 401


def test_query_success_returns_specs(client, make_token):
    _, headers = make_token()

    response = client.post("/vehicles/query", json=VALID_PAYLOAD, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert len(body["specs"]) == 2
    assert {s["attribute"] for s in body["specs"]} == {"horsepower", "torque"}
    assert all(s["available"] for s in body["specs"])


def test_query_upstream_failure_returns_502(client, make_token, claude_client):
    claude_client.should_fail = True
    _, headers = make_token()

    response = client.post("/vehicles/query", json=VALID_PAYLOAD, headers=headers)

    assert response.status_code == 502


def test_query_rejects_invalid_payload(client, make_token):
    _, headers = make_token()

    response = client.post(
        "/vehicles/query",
        json={"brand": "Ford; rm -rf /", "model": "Ranger", "version": "XL", "attributes": ["hp"]},
        headers=headers,
    )

    assert response.status_code == 422


def test_query_rejects_unknown_fields(client, make_token):
    _, headers = make_token()

    response = client.post(
        "/vehicles/query", json={**VALID_PAYLOAD, "extra": "field"}, headers=headers
    )

    assert response.status_code == 422


def test_list_queries_without_token_returns_401(client):
    response = client.get("/vehicles/queries")

    assert response.status_code == 401


def test_list_queries_returns_only_own_for_plain_user(client, make_token):
    user_id, headers = make_token(role=Role.USER)
    client.post("/vehicles/query", json=VALID_PAYLOAD, headers=headers)

    other_id, other_headers = make_token(role=Role.USER)
    client.post("/vehicles/query", json=VALID_PAYLOAD, headers=other_headers)

    response = client.get("/vehicles/queries", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_queries_returns_all_for_analyst(client, make_token):
    _, user_headers = make_token(role=Role.USER)
    client.post("/vehicles/query", json=VALID_PAYLOAD, headers=user_headers)

    _, analyst_headers = make_token(role=Role.ANALYST)
    client.post("/vehicles/query", json=VALID_PAYLOAD, headers=analyst_headers)

    response = client.get("/vehicles/queries", headers=analyst_headers)

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_query_unknown_id_returns_404(client, make_token):
    from uuid import uuid4

    _, headers = make_token()

    response = client.get(f"/vehicles/queries/{uuid4()}", headers=headers)

    assert response.status_code == 404


def test_get_query_owned_by_other_user_returns_403(client, make_token):
    _, owner_headers = make_token(role=Role.USER)
    created = client.post("/vehicles/query", json=VALID_PAYLOAD, headers=owner_headers).json()

    _, other_headers = make_token(role=Role.USER)
    response = client.get(f"/vehicles/queries/{created['id']}", headers=other_headers)

    assert response.status_code == 403


def test_get_query_visible_to_analyst_regardless_of_owner(client, make_token):
    _, owner_headers = make_token(role=Role.USER)
    created = client.post("/vehicles/query", json=VALID_PAYLOAD, headers=owner_headers).json()

    _, analyst_headers = make_token(role=Role.ANALYST)
    response = client.get(f"/vehicles/queries/{created['id']}", headers=analyst_headers)

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
