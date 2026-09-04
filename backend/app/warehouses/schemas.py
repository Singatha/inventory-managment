from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

WarehouseSortField = Literal["code", "name", "location", "created_at"]
SortOrder = Literal["asc", "desc"]


class WarehouseBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=32)
    location: str = Field(min_length=1, max_length=500)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("Warehouse code cannot be blank.")
        return normalized

    @field_validator("name", "location")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value cannot be blank.")
        return normalized


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    code: str | None = Field(default=None, min_length=1, max_length=32)
    location: str | None = Field(default=None, min_length=1, max_length=500)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("Warehouse code cannot be blank.")
        return normalized

    @field_validator("name", "location")
    @classmethod
    def strip_required_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value cannot be blank.")
        return normalized

    @model_validator(mode="after")
    def require_change(self) -> "WarehouseUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Warehouse fields cannot be null.")
        return self


class WarehouseResponse(WarehouseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class WarehouseListResponse(BaseModel):
    items: list[WarehouseResponse]
    total: int
    page: int
    page_size: int
