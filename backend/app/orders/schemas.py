from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator

from app.orders.models import OrderStatus

OrderSortField = Literal["order_number", "status", "created_at", "updated_at"]
SortOrder = Literal["asc", "desc"]


class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def reject_duplicate_inventory_lines(self) -> "OrderCreate":
        pairs = [(item.product_id, item.warehouse_id) for item in self.items]
        if len(pairs) != len(set(pairs)):
            raise ValueError("Each product and warehouse pair may only appear once.")
        return self


class OrderProductSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str
    is_active: bool


class OrderWarehouseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str


class OrderUserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    warehouse_id: int
    quantity: int
    unit_price: Decimal
    product: OrderProductSummary
    warehouse: OrderWarehouseSummary

    @field_serializer("unit_price", when_used="json")
    def serialize_unit_price(self, value: Decimal) -> float:
        return float(value)


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    status: OrderStatus
    created_by: int
    created_at: datetime
    updated_at: datetime
    total: Decimal
    creator: OrderUserSummary
    items: list[OrderItemResponse]

    @field_serializer("total", when_used="json")
    def serialize_total(self, value: Decimal) -> float:
        return float(value)


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int
