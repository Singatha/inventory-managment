import os
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, update

from app.core.database import async_session_factory
from app.main import app
from app.users.models import User

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION_TESTS") != "1",
        reason="Set RUN_INTEGRATION_TESTS=1 with a migrated PostgreSQL database.",
    ),
]


@pytest.fixture
async def registered_email() -> AsyncIterator[str]:
    email = f"auth-test-{uuid4()}@example.com"
    yield email
    async with async_session_factory() as session:
        await session.execute(delete(User).where(User.email == email))
        await session.commit()


@pytest.mark.asyncio
async def test_register_login_refresh_and_me(registered_email: str) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        registration = await client.post(
            "/api/auth/register",
            json={
                "email": registered_email,
                "password": "CorrectHorse123!",
                "first_name": "Integration",
                "last_name": "Test",
            },
        )
        assert registration.status_code == 201
        assert registration.json()["role"] == "EMPLOYEE"
        assert "password_hash" not in registration.json()

        login = await client.post(
            "/api/auth/login",
            json={"email": registered_email, "password": "CorrectHorse123!"},
        )
        assert login.status_code == 200
        tokens = login.json()

        current_user = await client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert current_user.status_code == 200
        assert current_user.json()["email"] == registered_email

        refresh_as_access = await client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
        )
        assert refresh_as_access.status_code == 401

        forbidden_users = await client.get(
            "/api/users", headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert forbidden_users.status_code == 403
        assert forbidden_users.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

        async with async_session_factory() as session:
            await session.execute(
                update(User).where(User.email == registered_email).values(role="ADMIN")
            )
            await session.commit()

        authorized_users = await client.get(
            "/api/users", headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert authorized_users.status_code == 200
        assert authorized_users.json()["total"] >= 1

        refreshed = await client.post(
            "/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert refreshed.status_code == 200
        assert refreshed.json()["refresh_token"] != tokens["refresh_token"]

        duplicate = await client.post(
            "/api/auth/register",
            json={
                "email": registered_email,
                "password": "CorrectHorse123!",
                "first_name": "Duplicate",
                "last_name": "User",
            },
        )
        assert duplicate.status_code == 409
        assert duplicate.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"
