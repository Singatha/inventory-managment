import os
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth.security import hash_password
from app.core.database import async_session_factory
from app.inventory.models import Inventory, StockMovement, StockMovementType
from app.main import app
from app.products.models import Product
from app.users.models import User, UserRole
from app.warehouses.models import Warehouse

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION_TESTS") != "1",
        reason="Set RUN_INTEGRATION_TESTS=1 with a migrated PostgreSQL database.",
    ),
]


@pytest.fixture
async def inventory_test_context() -> AsyncIterator[tuple[str, str, str]]:
    suffix = uuid4()
    marker = f"M4-{suffix.hex[:12]}"
    admin_email = f"inventory-admin-{suffix}@example.com"
    employee_email = f"inventory-employee-{suffix}@example.com"
    password = "CorrectHorse123!"
    async with async_session_factory() as session:
        session.add_all(
            [
                User(
                    email=admin_email,
                    password_hash=hash_password(password),
                    first_name="Inventory",
                    last_name="Admin",
                    role=UserRole.ADMIN,
                ),
                User(
                    email=employee_email,
                    password_hash=hash_password(password),
                    first_name="Inventory",
                    last_name="Employee",
                    role=UserRole.EMPLOYEE,
                ),
            ]
        )
        await session.commit()

    yield admin_email, employee_email, marker

    async with async_session_factory() as session:
        product_ids = select(Product.id).where(Product.sku.ilike(f"{marker}%"))
        warehouse_ids = select(Warehouse.id).where(Warehouse.code.ilike(f"{marker}%"))
        await session.execute(
            delete(StockMovement).where(StockMovement.product_id.in_(product_ids))
        )
        await session.execute(delete(Inventory).where(Inventory.product_id.in_(product_ids)))
        await session.execute(delete(Warehouse).where(Warehouse.id.in_(warehouse_ids)))
        await session.execute(delete(Product).where(Product.id.in_(product_ids)))
        await session.execute(
            User.__table__.delete().where(User.email.in_([admin_email, employee_email]))
        )
        await session.commit()


async def login(client: AsyncClient, email: str) -> str:
    response = await client.post(
        "/api/auth/login", json={"email": email, "password": "CorrectHorse123!"}
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


@pytest.mark.asyncio
async def test_warehouse_crud_and_transactional_inventory_operations(
    inventory_test_context: tuple[str, str, str],
) -> None:
    admin_email, employee_email, marker = inventory_test_context
    code = f"{marker}-JHB".upper()
    unused_code = f"{marker}-CPT".upper()
    sku = f"{marker}-SCANNER".upper()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        admin_headers = {"Authorization": f"Bearer {await login(client, admin_email)}"}
        employee_headers = {"Authorization": f"Bearer {await login(client, employee_email)}"}

        created = await client.post(
            "/api/warehouses",
            headers=admin_headers,
            json={
                "name": "Johannesburg Distribution Centre",
                "code": code.lower(),
                "location": "Midrand, Gauteng",
            },
        )
        assert created.status_code == 201
        warehouse = created.json()
        assert warehouse["code"] == code

        duplicate = await client.post(
            "/api/warehouses",
            headers=admin_headers,
            json={"name": "Duplicate", "code": code, "location": "Elsewhere"},
        )
        assert duplicate.status_code == 409
        assert duplicate.json()["error"]["code"] == "WAREHOUSE_CODE_ALREADY_EXISTS"

        employee_create = await client.post(
            "/api/warehouses",
            headers=employee_headers,
            json={"name": "Forbidden", "code": "NOPE", "location": "Nowhere"},
        )
        assert employee_create.status_code == 403

        listed = await client.get(
            "/api/warehouses", headers=employee_headers, params={"search": code}
        )
        assert listed.status_code == 200
        assert listed.json()["total"] == 1

        updated = await client.put(
            f"/api/warehouses/{warehouse['id']}",
            headers=admin_headers,
            json={"location": "Midrand, Johannesburg"},
        )
        assert updated.status_code == 200
        assert updated.json()["location"] == "Midrand, Johannesburg"

        unused = await client.post(
            "/api/warehouses",
            headers=admin_headers,
            json={"name": "Cape Town Overflow", "code": unused_code, "location": "Cape Town"},
        )
        assert unused.status_code == 201

        product_response = await client.post(
            "/api/products",
            headers=admin_headers,
            json={
                "sku": sku,
                "name": "Barcode Scanner",
                "category": "Warehouse equipment",
                "price": "1499.00",
                "reorder_level": 5,
            },
        )
        assert product_response.status_code == 201
        product = product_response.json()

        employee_receipt = await client.post(
            "/api/inventory/receive",
            headers=employee_headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": 10,
            },
        )
        assert employee_receipt.status_code == 403

        receipt = await client.post(
            "/api/inventory/receive",
            headers=admin_headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": 10,
                "notes": "  Opening delivery  ",
            },
        )
        assert receipt.status_code == 201
        assert receipt.json()["inventory"]["available_quantity"] == 10
        assert receipt.json()["movement"]["type"] == "RECEIVE"
        assert receipt.json()["movement"]["notes"] == "Opening delivery"

        adjustment = await client.post(
            "/api/inventory/adjust",
            headers=admin_headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": -6,
                "reason": "Cycle count correction",
            },
        )
        assert adjustment.status_code == 201
        adjusted = adjustment.json()
        assert adjusted["inventory"]["quantity_on_hand"] == 4
        assert adjusted["inventory"]["available_quantity"] == 4
        assert adjusted["inventory"]["is_low_stock"] is True
        assert adjusted["movement"]["type"] == "ADJUSTMENT"
        assert adjusted["movement"]["quantity"] == -6

        invalid_adjustment = await client.post(
            "/api/inventory/adjust",
            headers=admin_headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": -5,
                "reason": "Impossible count",
            },
        )
        assert invalid_adjustment.status_code == 409
        assert invalid_adjustment.json()["error"]["code"] == "INSUFFICIENT_STOCK"

        inventory = await client.get(
            "/api/inventory",
            headers=employee_headers,
            params={"search": sku, "low_stock": True},
        )
        assert inventory.status_code == 200
        inventory_data = inventory.json()
        assert inventory_data["total"] == 1
        assert inventory_data["total_quantity_on_hand"] == 4
        assert inventory_data["total_available_quantity"] == 4
        assert inventory_data["low_stock_count"] == 1

        by_product = await client.get(
            f"/api/inventory/{product['id']}", headers=employee_headers
        )
        by_warehouse = await client.get(
            f"/api/inventory/warehouse/{warehouse['id']}", headers=employee_headers
        )
        assert by_product.status_code == 200
        assert by_product.json()["total"] == 1
        assert by_warehouse.status_code == 200
        assert by_warehouse.json()["total"] == 1

        in_use_delete = await client.delete(
            f"/api/warehouses/{warehouse['id']}", headers=admin_headers
        )
        assert in_use_delete.status_code == 409
        assert in_use_delete.json()["error"]["code"] == "WAREHOUSE_IN_USE"

        unused_delete = await client.delete(
            f"/api/warehouses/{unused.json()['id']}", headers=admin_headers
        )
        assert unused_delete.status_code == 204

    async with async_session_factory() as session:
        movements = list(
            (
                await session.scalars(
                    select(StockMovement)
                    .where(StockMovement.product_id == product["id"])
                    .order_by(StockMovement.id)
                )
            ).all()
        )
        assert [movement.type for movement in movements] == [
            StockMovementType.RECEIVE,
            StockMovementType.ADJUSTMENT,
        ]
        assert [movement.quantity for movement in movements] == [10, -6]
