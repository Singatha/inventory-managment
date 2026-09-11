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
from app.orders.models import Order, OrderItem
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
async def order_test_context() -> AsyncIterator[tuple[str, str, str]]:
    suffix = uuid4()
    marker = f"M6-{suffix.hex[:12]}".upper()
    admin_email = f"order-admin-{suffix}@example.com"
    employee_email = f"order-employee-{suffix}@example.com"
    password = "CorrectHorse123!"
    async with async_session_factory() as session:
        session.add_all(
            [
                User(
                    email=admin_email,
                    password_hash=hash_password(password),
                    first_name="Order",
                    last_name="Admin",
                    role=UserRole.ADMIN,
                ),
                User(
                    email=employee_email,
                    password_hash=hash_password(password),
                    first_name="Order",
                    last_name="Employee",
                    role=UserRole.EMPLOYEE,
                ),
            ]
        )
        await session.commit()

    yield admin_email, employee_email, marker

    async with async_session_factory() as session:
        product_ids = select(Product.id).where(Product.sku.ilike(f"{marker}%"))
        user_ids = select(User.id).where(User.email.in_([admin_email, employee_email]))
        owned_order_ids = select(Order.id).where(Order.created_by.in_(user_ids))
        await session.execute(
            delete(StockMovement).where(StockMovement.product_id.in_(product_ids))
        )
        await session.execute(delete(OrderItem).where(OrderItem.order_id.in_(owned_order_ids)))
        await session.execute(delete(Order).where(Order.id.in_(owned_order_ids)))
        await session.execute(delete(Inventory).where(Inventory.product_id.in_(product_ids)))
        await session.execute(delete(Warehouse).where(Warehouse.code.ilike(f"{marker}%")))
        await session.execute(delete(Product).where(Product.id.in_(product_ids)))
        await session.execute(delete(User).where(User.id.in_(user_ids)))
        await session.commit()


async def login(client: AsyncClient, email: str) -> dict[str, str]:
    response = await client.post(
        "/api/auth/login", json={"email": email, "password": "CorrectHorse123!"}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.asyncio
async def test_order_lifecycle_reservations_permissions_and_audit(
    order_test_context: tuple[str, str, str],
) -> None:
    admin_email, employee_email, marker = order_test_context
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        admin_headers = await login(client, admin_email)
        employee_headers = await login(client, employee_email)
        warehouse_response = await client.post(
            "/api/warehouses",
            headers=admin_headers,
            json={"name": "Order warehouse", "code": marker, "location": "Johannesburg"},
        )
        product_response = await client.post(
            "/api/products",
            headers=admin_headers,
            json={
                "sku": f"{marker}-ITEM",
                "name": "Order item",
                "category": "Tests",
                "price": "25.50",
                "reorder_level": 2,
            },
        )
        warehouse = warehouse_response.json()
        product = product_response.json()
        await client.post(
            "/api/inventory/receive",
            headers=admin_headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": 10,
            },
        )

        created = await client.post(
            "/api/orders",
            headers=employee_headers,
            json={
                "items": [
                    {
                        "product_id": product["id"],
                        "warehouse_id": warehouse["id"],
                        "quantity": 6,
                    }
                ]
            },
        )
        assert created.status_code == 201
        order = created.json()
        assert order["status"] == "PENDING"
        assert order["order_number"].startswith("SO-")
        assert order["total"] == 153.0
        assert order["items"][0]["unit_price"] == 25.5

        forbidden = await client.post(
            f"/api/orders/{order['id']}/confirm", headers=employee_headers
        )
        assert forbidden.status_code == 403
        invalid = await client.post(
            f"/api/orders/{order['id']}/process", headers=admin_headers
        )
        assert invalid.status_code == 409
        assert invalid.json()["error"]["code"] == "ORDER_TRANSITION_INVALID"

        confirmed = await client.post(
            f"/api/orders/{order['id']}/confirm", headers=admin_headers
        )
        assert confirmed.status_code == 200
        assert confirmed.json()["status"] == "CONFIRMED"
        inventory = await client.get(
            "/api/inventory", headers=employee_headers, params={"product_id": product["id"]}
        )
        assert inventory.json()["items"][0]["quantity_reserved"] == 6
        assert inventory.json()["items"][0]["available_quantity"] == 4

        employee_cancel = await client.post(
            f"/api/orders/{order['id']}/cancel", headers=employee_headers
        )
        assert employee_cancel.status_code == 403
        assert (
            await client.post(f"/api/orders/{order['id']}/process", headers=admin_headers)
        ).status_code == 200
        shipped = await client.post(
            f"/api/orders/{order['id']}/ship", headers=admin_headers
        )
        assert shipped.status_code == 200
        assert shipped.json()["status"] == "SHIPPED"
        completed = await client.post(
            f"/api/orders/{order['id']}/complete", headers=admin_headers
        )
        assert completed.status_code == 200
        assert completed.json()["status"] == "COMPLETED"

        insufficient = await client.post(
            "/api/orders",
            headers=employee_headers,
            json={
                "items": [
                    {
                        "product_id": product["id"],
                        "warehouse_id": warehouse["id"],
                        "quantity": 5,
                    }
                ]
            },
        )
        insufficient_confirmation = await client.post(
            f"/api/orders/{insufficient.json()['id']}/confirm", headers=admin_headers
        )
        assert insufficient_confirmation.status_code == 409
        assert insufficient_confirmation.json()["error"]["code"] == "INSUFFICIENT_STOCK"
        own_pending_cancellation = await client.post(
            f"/api/orders/{insufficient.json()['id']}/cancel", headers=employee_headers
        )
        assert own_pending_cancellation.status_code == 200
        assert own_pending_cancellation.json()["status"] == "CANCELLED"

        cancellable = await client.post(
            "/api/orders",
            headers=employee_headers,
            json={
                "items": [
                    {
                        "product_id": product["id"],
                        "warehouse_id": warehouse["id"],
                        "quantity": 3,
                    }
                ]
            },
        )
        await client.post(
            f"/api/orders/{cancellable.json()['id']}/confirm", headers=admin_headers
        )
        cancelled = await client.post(
            f"/api/orders/{cancellable.json()['id']}/cancel", headers=admin_headers
        )
        assert cancelled.status_code == 200
        assert cancelled.json()["status"] == "CANCELLED"

        listed = await client.get(
            "/api/orders", headers=employee_headers, params={"search": order["order_number"]}
        )
        assert listed.status_code == 200
        assert listed.json()["total"] == 1

    async with async_session_factory() as session:
        balance = await session.scalar(
            select(Inventory).where(
                Inventory.product_id == product["id"],
                Inventory.warehouse_id == warehouse["id"],
            )
        )
        assert balance is not None
        assert balance.quantity_on_hand == 4
        assert balance.quantity_reserved == 0
        movements = list(
            (
                await session.scalars(
                    select(StockMovement)
                    .where(StockMovement.reference_type == "ORDER")
                    .where(StockMovement.product_id == product["id"])
                    .order_by(StockMovement.id)
                )
            ).all()
        )
        assert [movement.type for movement in movements] == [
            StockMovementType.RESERVE,
            StockMovementType.SHIPMENT,
            StockMovementType.RESERVE,
            StockMovementType.RELEASE,
        ]
        assert [movement.quantity for movement in movements] == [-6, -6, -3, 3]
