import pytest
from pydantic import ValidationError

from app.inventory.schemas import StockAdjustment, StockReceive, StockTransfer
from app.warehouses.schemas import WarehouseCreate, WarehouseUpdate


def test_warehouse_create_normalizes_fields() -> None:
    warehouse = WarehouseCreate(
        name="  Johannesburg Distribution Centre ",
        code=" jhb-01 ",
        location="  Midrand, Gauteng ",
    )

    assert warehouse.name == "Johannesburg Distribution Centre"
    assert warehouse.code == "JHB-01"
    assert warehouse.location == "Midrand, Gauteng"


@pytest.mark.parametrize("field", ["name", "code", "location"])
def test_warehouse_create_rejects_blank_fields(field: str) -> None:
    data = {"name": "Johannesburg", "code": "JHB-01", "location": "Gauteng"}
    data[field] = "   "

    with pytest.raises(ValidationError):
        WarehouseCreate.model_validate(data)


def test_warehouse_update_requires_a_change() -> None:
    with pytest.raises(ValidationError):
        WarehouseUpdate()

    with pytest.raises(ValidationError):
        WarehouseUpdate(name=None)


def test_receive_requires_positive_quantity_and_normalizes_notes() -> None:
    receipt = StockReceive(product_id=1, warehouse_id=2, quantity=8, notes="  PO delivery  ")
    assert receipt.notes == "PO delivery"

    with pytest.raises(ValidationError):
        StockReceive(product_id=1, warehouse_id=2, quantity=0)


@pytest.mark.parametrize("quantity", [-4, 4])
def test_adjustment_accepts_signed_non_zero_quantity(quantity: int) -> None:
    adjustment = StockAdjustment(
        product_id=1,
        warehouse_id=2,
        quantity=quantity,
        reason="  Cycle count  ",
    )
    assert adjustment.quantity == quantity
    assert adjustment.reason == "Cycle count"


@pytest.mark.parametrize(
    ("quantity", "reason"),
    [(0, "Cycle count"), (1, "   ")],
)
def test_adjustment_rejects_zero_quantity_or_blank_reason(
    quantity: int, reason: str
) -> None:
    with pytest.raises(ValidationError):
        StockAdjustment(
            product_id=1,
            warehouse_id=2,
            quantity=quantity,
            reason=reason,
        )


def test_transfer_requires_distinct_warehouses_and_positive_quantity() -> None:
    transfer = StockTransfer(
        product_id=1,
        source_warehouse_id=2,
        destination_warehouse_id=3,
        quantity=4,
        notes="  Rebalance stock  ",
    )
    assert transfer.notes == "Rebalance stock"

    with pytest.raises(ValidationError):
        StockTransfer(
            product_id=1,
            source_warehouse_id=2,
            destination_warehouse_id=2,
            quantity=4,
        )

    with pytest.raises(ValidationError):
        StockTransfer(
            product_id=1,
            source_warehouse_id=2,
            destination_warehouse_id=3,
            quantity=0,
        )
