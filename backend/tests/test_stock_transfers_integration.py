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
async def transfer_test_context() -> AsyncIterator[tuple[str, str, str]]:
    suffix = uuid4()
    marker = f"M5-{suffix.hex[:12]}"
    manager_email = f"transfer-manager-{suffix}@example.com"
    employee_email = f"transfer-employee-{suffix}@example.com"
    password = "CorrectHorse123!"
    async with async_session_factory() as session:
        session.add_all(
            [
                User(
                    email=manager_email,
                    password_hash=hash_password(password),
                    first_name="Transfer",
                    last_name="Manager",
                    role=UserRole.WAREHOUSE_MANAGER,
                ),
                User(
                    email=employee_email,
                    password_hash=hash_password(password),
                    first_name="Transfer",
                    last_name="Employee",
                    role=UserRole.EMPLOYEE,
                ),
            ]
        )
        await session.commit()

    yield manager_email, employee_email, marker

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
            User.__table__.delete().where(User.email.in_([manager_email, employee_email]))
        )
        await session.commit()


async def login(client: AsyncClient, email: str) -> str:
    response = await client.post(
        "/api/auth/login", json={"email": email, "password": "CorrectHorse123!"}
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


@pytest.mark.asyncio
async def test_atomic_transfer_and_filterable_movement_history(
    transfer_test_context: tuple[str, str, str],
) -> None:
    manager_email, employee_email, marker = transfer_test_context
    sku = f"{marker}-ROUTER".upper()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        manager_headers = {"Authorization": f"Bearer {await login(client, manager_email)}"}
        employee_headers = {"Authorization": f"Bearer {await login(client, employee_email)}"}

        product_response = await client.post(
            "/api/products",
            headers=manager_headers,
            json={
                "sku": sku,
                "name": "Wi-Fi Router",
                "category": "Networking",
                "price": "2499.00",
                "reorder_level": 2,
            },
        )
        assert product_response.status_code == 201
        product = product_response.json()

        warehouses = []
        for suffix, name, location in [
            ("JHB", "Johannesburg DC", "Midrand"),
            ("CPT", "Cape Town DC", "Montague Gardens"),
        ]:
            response = await client.post(
                "/api/warehouses",
                headers=manager_headers,
                json={"code": f"{marker}-{suffix}", "name": name, "location": location},
            )
            assert response.status_code == 201
            warehouses.append(response.json())
        source, destination = warehouses

        receipt = await client.post(
            "/api/inventory/receive",
            headers=manager_headers,
            json={
                "product_id": product["id"],
                "warehouse_id": source["id"],
                "quantity": 10,
                "notes": "Opening stock",
            },
        )
        assert receipt.status_code == 201

        employee_transfer = await client.post(
            "/api/inventory/transfer",
            headers=employee_headers,
            json={
                "product_id": product["id"],
                "source_warehouse_id": source["id"],
                "destination_warehouse_id": destination["id"],
                "quantity": 1,
            },
        )
        assert employee_transfer.status_code == 403

        transfer = await client.post(
            "/api/inventory/transfer",
            headers=manager_headers,
            json={
                "product_id": product["id"],
                "source_warehouse_id": source["id"],
                "destination_warehouse_id": destination["id"],
                "quantity": 4,
                "notes": "  Regional replenishment  ",
            },
        )
        assert transfer.status_code == 201
        transfer_data = transfer.json()
        assert transfer_data["source_inventory"]["quantity_on_hand"] == 6
        assert transfer_data["destination_inventory"]["quantity_on_hand"] == 4
        transfer_out, transfer_in = transfer_data["movements"]
        assert transfer_out["type"] == "TRANSFER_OUT"
        assert transfer_out["quantity"] == -4
        assert transfer_in["type"] == "TRANSFER_IN"
        assert transfer_in["quantity"] == 4
        assert transfer_out["reference_type"] == "TRANSFER"
        assert transfer_out["reference_id"] == transfer_in["reference_id"]
        assert transfer_out["notes"] == "Regional replenishment"

        insufficient = await client.post(
            "/api/inventory/transfer",
            headers=manager_headers,
            json={
                "product_id": product["id"],
                "source_warehouse_id": source["id"],
                "destination_warehouse_id": destination["id"],
                "quantity": 7,
            },
        )
        assert insufficient.status_code == 409
        assert insufficient.json()["error"]["code"] == "INSUFFICIENT_STOCK"

        same_warehouse = await client.post(
            "/api/inventory/transfer",
            headers=manager_headers,
            json={
                "product_id": product["id"],
                "source_warehouse_id": source["id"],
                "destination_warehouse_id": source["id"],
                "quantity": 1,
            },
        )
        assert same_warehouse.status_code == 422

        history = await client.get(
            "/api/stock-movements",
            headers=employee_headers,
            params={
                "search": sku,
                "warehouse_id": source["id"],
                "movement_type": "TRANSFER_OUT",
            },
        )
        assert history.status_code == 200
        history_data = history.json()
        assert history_data["total"] == 1
        movement = history_data["items"][0]
        assert movement["product"]["sku"] == sku
        assert movement["warehouse"]["code"] == source["code"]
        assert movement["creator"]["first_name"] == "Transfer"

        detail = await client.get(
            f"/api/stock-movements/{movement['id']}", headers=employee_headers
        )
        assert detail.status_code == 200
        assert detail.json()["reference_id"] == transfer_out["reference_id"]

        all_history = await client.get(
            "/api/stock-movements",
            headers=employee_headers,
            params={"product_id": product["id"]},
        )
        assert all_history.status_code == 200
        assert all_history.json()["total"] == 3

    async with async_session_factory() as session:
        balances = list(
            (
                await session.scalars(
                    select(Inventory)
                    .where(Inventory.product_id == product["id"])
                    .order_by(Inventory.warehouse_id)
                )
            ).all()
        )
        movements = list(
            (
                await session.scalars(
                    select(StockMovement).where(StockMovement.product_id == product["id"])
                )
            ).all()
        )
        assert sorted(balance.quantity_on_hand for balance in balances) == [4, 6]
        assert [movement.type for movement in movements].count(
            StockMovementType.TRANSFER_OUT
        ) == 1
        assert [movement.type for movement in movements].count(
            StockMovementType.TRANSFER_IN
        ) == 1
        assert len(movements) == 3
