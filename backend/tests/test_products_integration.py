import os
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.auth.security import hash_password
from app.core.database import async_session_factory
from app.main import app
from app.products.models import Product
from app.users.models import User, UserRole

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION_TESTS") != "1",
        reason="Set RUN_INTEGRATION_TESTS=1 with a migrated PostgreSQL database.",
    ),
]


@pytest.fixture
async def product_test_users() -> AsyncIterator[tuple[str, str]]:
    suffix = uuid4()
    admin_email = f"product-admin-{suffix}@example.com"
    employee_email = f"product-employee-{suffix}@example.com"
    password = "CorrectHorse123!"
    async with async_session_factory() as session:
        session.add_all(
            [
                User(
                    email=admin_email,
                    password_hash=hash_password(password),
                    first_name="Product",
                    last_name="Admin",
                    role=UserRole.ADMIN,
                ),
                User(
                    email=employee_email,
                    password_hash=hash_password(password),
                    first_name="Product",
                    last_name="Employee",
                    role=UserRole.EMPLOYEE,
                ),
            ]
        )
        await session.commit()

    yield admin_email, employee_email

    async with async_session_factory() as session:
        await session.execute(delete(Product).where(Product.sku.ilike(f"M3-{suffix}%")))
        user_delete = User.__table__.delete().where(
            User.email.in_([admin_email, employee_email])
        )
        await session.execute(user_delete)
        await session.commit()


async def login(client: AsyncClient, email: str) -> str:
    response = await client.post(
        "/api/auth/login", json={"email": email, "password": "CorrectHorse123!"}
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


@pytest.mark.asyncio
async def test_product_crud_filters_permissions_and_soft_delete(
    product_test_users: tuple[str, str],
) -> None:
    admin_email, employee_email = product_test_users
    suffix = admin_email.split("product-admin-")[1].split("@")[0]
    sku = f"M3-{suffix}-LAPTOP".upper()
    second_sku = f"M3-{suffix}-MONITOR".upper()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        admin_token = await login(client, admin_email)
        employee_token = await login(client, employee_email)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        employee_headers = {"Authorization": f"Bearer {employee_token}"}

        created = await client.post(
            "/api/products",
            headers=admin_headers,
            json={
                "sku": sku.lower(),
                "name": "Latitude 7450",
                "description": "Business laptop",
                "category": "Laptops",
                "price": "24999.95",
                "reorder_level": 5,
            },
        )
        assert created.status_code == 201
        product = created.json()
        assert product["sku"] == sku
        assert product["price"] == 24999.95

        second_created = await client.post(
            "/api/products",
            headers=admin_headers,
            json={
                "sku": second_sku,
                "name": "UltraSharp Monitor",
                "category": "Displays",
                "price": "8999.00",
                "reorder_level": 3,
            },
        )
        assert second_created.status_code == 201

        details = await client.get(
            f"/api/products/{product['id']}", headers=employee_headers
        )
        assert details.status_code == 200
        assert details.json()["sku"] == sku

        categories = await client.get("/api/products/categories", headers=employee_headers)
        assert categories.status_code == 200
        assert {"Displays", "Laptops"}.issubset(categories.json())

        duplicate = await client.post(
            "/api/products",
            headers=admin_headers,
            json={
                "sku": sku,
                "name": "Duplicate",
                "category": "Laptops",
                "price": "1.00",
            },
        )
        assert duplicate.status_code == 409
        assert duplicate.json()["error"]["code"] == "SKU_ALREADY_EXISTS"

        employee_create = await client.post(
            "/api/products",
            headers=employee_headers,
            json={"sku": "NOPE", "name": "Nope", "category": "Other", "price": "1.00"},
        )
        assert employee_create.status_code == 403

        filtered = await client.get(
            "/api/products",
            headers=employee_headers,
            params={"search": sku, "category": "laptops", "is_active": True},
        )
        assert filtered.status_code == 200
        assert filtered.json()["total"] == 1
        assert filtered.json()["items"][0]["id"] == product["id"]

        updated = await client.put(
            f"/api/products/{product['id']}",
            headers=admin_headers,
            json={"name": "Latitude 7450 Gen 2", "price": "23999.95"},
        )
        assert updated.status_code == 200
        assert updated.json()["name"] == "Latitude 7450 Gen 2"

        deleted = await client.delete(f"/api/products/{product['id']}", headers=admin_headers)
        assert deleted.status_code == 204

        inactive = await client.get(
            "/api/products", headers=employee_headers, params={"is_active": False, "search": sku}
        )
        assert inactive.status_code == 200
        assert inactive.json()["total"] == 1
        assert inactive.json()["items"][0]["is_active"] is False
