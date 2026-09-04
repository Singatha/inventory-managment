from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.inventory.models import StockMovementType

InventorySortField = Literal[
    "product", "warehouse", "quantity_on_hand", "quantity_reserved", "available_quantity"
]
SortOrder = Literal["asc", "desc"]


class ProductInventorySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str
    reorder_level: int
    is_active: bool


class WarehouseInventorySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    location: str


class InventoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    warehouse_id: int
    quantity_on_hand: int
    quantity_reserved: int
    available_quantity: int
    is_low_stock: bool
    updated_at: datetime
    product: ProductInventorySummary
    warehouse: WarehouseInventorySummary


class InventoryListResponse(BaseModel):
    items: list[InventoryResponse]
    total: int
    page: int
    page_size: int
    total_quantity_on_hand: int
    total_quantity_reserved: int
    total_available_quantity: int
    low_stock_count: int


class StockReceive(BaseModel):
    product_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class StockAdjustment(BaseModel):
    product_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)
    quantity: int
    reason: str = Field(min_length=1, max_length=2000)

    @field_validator("quantity")
    @classmethod
    def reject_zero_quantity(cls, value: int) -> int:
        if value == 0:
            raise ValueError("Adjustment quantity cannot be zero.")
        return value

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("An adjustment reason is required.")
        return normalized


class StockTransfer(BaseModel):
    product_id: int = Field(gt=0)
    source_warehouse_id: int = Field(gt=0)
    destination_warehouse_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def require_different_warehouses(self) -> "StockTransfer":
        if self.source_warehouse_id == self.destination_warehouse_id:
            raise ValueError("Source and destination warehouses must be different.")
        return self


class StockMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    warehouse_id: int
    type: StockMovementType
    quantity: int
    reference_type: str | None
    reference_id: int | None
    notes: str | None
    created_by: int
    created_at: datetime


class InventoryOperationResponse(BaseModel):
    inventory: InventoryResponse
    movement: StockMovementResponse


class MovementUserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str


class StockMovementDetailResponse(StockMovementResponse):
    product: ProductInventorySummary
    warehouse: WarehouseInventorySummary
    creator: MovementUserSummary


class StockMovementListResponse(BaseModel):
    items: list[StockMovementDetailResponse]
    total: int
    page: int
    page_size: int


class StockTransferResponse(BaseModel):
    source_inventory: InventoryResponse
    destination_inventory: InventoryResponse
    movements: list[StockMovementResponse]
