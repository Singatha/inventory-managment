from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.products.schemas import ProductCreate, ProductUpdate


def test_product_create_normalizes_text_fields() -> None:
    product = ProductCreate(
        sku="  lap-001 ",
        name="  Latitude 7450 ",
        description="  Business laptop  ",
        category="  Laptops ",
        price=Decimal("24999.95"),
        reorder_level=5,
    )

    assert product.sku == "LAP-001"
    assert product.name == "Latitude 7450"
    assert product.category == "Laptops"
    assert product.description == "Business laptop"


@pytest.mark.parametrize(
    ("field", "value"),
    [("price", Decimal("-0.01")), ("reorder_level", -1)],
)
def test_product_create_rejects_negative_values(field: str, value: object) -> None:
    data = {
        "sku": "LAP-001",
        "name": "Latitude 7450",
        "category": "Laptops",
        "price": Decimal("1.00"),
        "reorder_level": 0,
    }
    data[field] = value

    with pytest.raises(ValidationError):
        ProductCreate.model_validate(data)


def test_product_update_requires_at_least_one_field() -> None:
    with pytest.raises(ValidationError):
        ProductUpdate()


@pytest.mark.parametrize("field", ["sku", "name", "category"])
def test_product_create_rejects_blank_required_text(field: str) -> None:
    data = {
        "sku": "LAP-001",
        "name": "Latitude 7450",
        "category": "Laptops",
        "price": Decimal("1.00"),
    }
    data[field] = "   "

    with pytest.raises(ValidationError):
        ProductCreate.model_validate(data)
