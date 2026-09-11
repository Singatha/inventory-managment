import pytest
from pydantic import ValidationError

from app.orders.schemas import OrderCreate


def test_order_requires_at_least_one_positive_line() -> None:
    with pytest.raises(ValidationError):
        OrderCreate(items=[])

    with pytest.raises(ValidationError):
        OrderCreate(items=[{"product_id": 1, "warehouse_id": 2, "quantity": 0}])


def test_order_rejects_duplicate_product_warehouse_pairs() -> None:
    with pytest.raises(ValidationError):
        OrderCreate(
            items=[
                {"product_id": 1, "warehouse_id": 2, "quantity": 1},
                {"product_id": 1, "warehouse_id": 2, "quantity": 3},
            ]
        )


def test_order_accepts_same_product_from_different_warehouses() -> None:
    order = OrderCreate(
        items=[
            {"product_id": 1, "warehouse_id": 2, "quantity": 1},
            {"product_id": 1, "warehouse_id": 3, "quantity": 3},
        ]
    )

    assert len(order.items) == 2
