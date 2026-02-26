"""
Integration tests for the REST API endpoints.
Uses in-memory SQLite via the shared client fixture.
"""

import pytest
import pytest_asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _register_and_login(client, username="hero", password="secret99", email=None):
    email = email or f"{username}@test.com"
    await client.post(
        "/auth/register",
        json={"username": username, "password": password, "email": email},
    )
    resp = await client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def token(client):
    return await _register_and_login(client)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_and_login(client):
    resp = await client.post(
        "/auth/register",
        json={"username": "newuser1", "password": "pw1234ab", "email": "newuser1@test.com"},
    )
    assert resp.status_code == 201
    resp2 = await client.post(
        "/auth/login",
        data={"username": "newuser1", "password": "pw1234ab"},
    )
    assert resp2.status_code == 200
    assert "access_token" in resp2.json()


@pytest.mark.asyncio
async def test_register_duplicate(client):
    body = {"username": "dupuser", "password": "pw1234ab", "email": "dup@test.com"}
    await client.post("/auth/register", json=body)
    resp = await client.post("/auth/register", json=body)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_bad_password(client):
    await client.post(
        "/auth/register",
        json={"username": "badpw", "password": "correct1", "email": "badpw@test.com"},
    )
    resp = await client.post("/auth/login", data={"username": "badpw", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint(client, token):
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "hero"


@pytest.mark.asyncio
async def test_me_no_token(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Worlds
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_worlds_empty(client):
    resp = await client.get("/worlds/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
