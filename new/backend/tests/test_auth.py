"""Tests for auth endpoints: register, login, /me."""

import pytest


@pytest.mark.asyncio
async def test_register_and_login(client):
    # Register
    resp = await client.post("/auth/register", json={
        "username": "testplayer",
        "email": "test@example.com",
        "password": "secret123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "testplayer"
    assert "id" in data

    # Login
    resp = await client.post("/auth/login", data={
        "username": "testplayer",
        "password": "secret123",
    })
    assert resp.status_code == 200
    token_data = resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # /me
    token = token_data["access_token"]
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "testplayer"


@pytest.mark.asyncio
async def test_duplicate_username(client):
    payload = {"username": "dup_user", "email": "dup@example.com", "password": "pw"}
    await client.post("/auth/register", json=payload)
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_wrong_password(client):
    await client.post("/auth/register", json={
        "username": "wrongpw",
        "email": "wrongpw@example.com",
        "password": "correct",
    })
    resp = await client.post("/auth/login", data={"username": "wrongpw", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_me(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401
