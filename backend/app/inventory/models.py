from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Identity,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.products.models import Product
    from app.warehouses.models import Warehouse


class StockMovementType(StrEnum):
    RECEIVE = "RECEIVE"
    ADJUSTMENT = "ADJUSTMENT"
    RESERVE = "RESERVE"
    RELEASE = "RELEASE"
    SHIPMENT = "SHIPMENT"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    RETURN = "RETURN"


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint("product_id", "warehouse_id", name="uq_inventory_product_warehouse"),
        CheckConstraint(
            "quantity_on_hand >= 0", name="ck_inventory_quantity_on_hand_non_negative"
        ),
        CheckConstraint(
            "quantity_reserved >= 0", name="ck_inventory_quantity_reserved_non_negative"
        ),
        CheckConstraint(
            "quantity_reserved <= quantity_on_hand",
            name="ck_inventory_reserved_not_above_on_hand",
        ),
        Index("ix_inventory_product_id", "product_id"),
        Index("ix_inventory_warehouse_id", "warehouse_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    warehouse_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False
    )
    quantity_on_hand: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quantity_reserved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    product: Mapped[Product] = relationship(lazy="raise")
    warehouse: Mapped[Warehouse] = relationship(lazy="raise")

    @property
    def available_quantity(self) -> int:
        return self.quantity_on_hand - self.quantity_reserved

    @property
    def is_low_stock(self) -> bool:
        return self.available_quantity <= self.product.reorder_level


class StockMovement(Base):
    __tablename__ = "stock_movements"
    __table_args__ = (
        CheckConstraint("quantity <> 0", name="ck_stock_movements_quantity_non_zero"),
        Index("ix_stock_movements_product_warehouse", "product_id", "warehouse_id"),
        Index("ix_stock_movements_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    warehouse_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False
    )
    type: Mapped[StockMovementType] = mapped_column(
        Enum(StockMovementType, name="stock_movement_type"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
