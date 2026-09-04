from datetime import datetime
from typing import cast

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.inventory.models import Inventory, StockMovement, StockMovementType
from app.inventory.schemas import InventorySortField, SortOrder
from app.products.models import Product
from app.warehouses.models import Warehouse


class InventoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_inventory(
        self,
        *,
        offset: int,
        limit: int,
        search: str | None,
        product_id: int | None,
        warehouse_id: int | None,
        low_stock: bool | None,
        sort_by: InventorySortField,
        sort_order: SortOrder,
    ) -> tuple[list[Inventory], int, int, int, int]:
        filters = []
        available = Inventory.quantity_on_hand - Inventory.quantity_reserved
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Product.sku.ilike(pattern),
                    Product.name.ilike(pattern),
                    Warehouse.code.ilike(pattern),
                    Warehouse.name.ilike(pattern),
                )
            )
        if product_id is not None:
            filters.append(Inventory.product_id == product_id)
        if warehouse_id is not None:
            filters.append(Inventory.warehouse_id == warehouse_id)
        if low_stock is not None:
            low_stock_expression = available <= Product.reorder_level
            filters.append(low_stock_expression if low_stock else ~low_stock_expression)

        base = select(Inventory).join(Product).join(Warehouse).where(*filters)
        count_statement = (
            select(func.count()).select_from(Inventory).join(Product).join(Warehouse).where(*filters)
        )
        summary_statement = (
            select(
                func.coalesce(func.sum(Inventory.quantity_on_hand), 0),
                func.coalesce(func.sum(Inventory.quantity_reserved), 0),
                func.count().filter(available <= Product.reorder_level),
            )
            .select_from(Inventory)
            .join(Product)
            .join(Warehouse)
            .where(*filters)
        )
        sort_columns = {
            "product": Product.name,
            "warehouse": Warehouse.name,
            "quantity_on_hand": Inventory.quantity_on_hand,
            "quantity_reserved": Inventory.quantity_reserved,
            "available_quantity": available,
        }
        sort_column = sort_columns[sort_by]
        ordering = sort_column.desc() if sort_order == "desc" else sort_column.asc()
        statement = (
            base.options(selectinload(Inventory.product), selectinload(Inventory.warehouse))
            .order_by(ordering, Inventory.id.asc())
            .offset(offset)
            .limit(limit)
        )

        inventory = list((await self.session.scalars(statement)).all())
        total = int(await self.session.scalar(count_statement) or 0)
        summary = (await self.session.execute(summary_statement)).one()
        return inventory, total, int(summary[0]), int(summary[1]), int(summary[2])

    async def get_for_update(self, product_id: int, warehouse_id: int) -> Inventory | None:
        statement = (
            select(Inventory)
            .where(
                Inventory.product_id == product_id,
                Inventory.warehouse_id == warehouse_id,
            )
            .with_for_update()
        )
        return cast(Inventory | None, await self.session.scalar(statement))

    async def get_with_details(self, inventory_id: int) -> Inventory | None:
        statement = (
            select(Inventory)
            .where(Inventory.id == inventory_id)
            .options(selectinload(Inventory.product), selectinload(Inventory.warehouse))
        )
        return cast(Inventory | None, await self.session.scalar(statement))

    async def get_transfer_rows_for_update(
        self, product_id: int, warehouse_ids: tuple[int, int]
    ) -> dict[int, Inventory]:
        statement = (
            select(Inventory)
            .where(
                Inventory.product_id == product_id,
                Inventory.warehouse_id.in_(warehouse_ids),
            )
            .order_by(Inventory.warehouse_id.asc())
            .with_for_update()
        )
        rows = (await self.session.scalars(statement)).all()
        return {row.warehouse_id: row for row in rows}

    async def list_movements(
        self,
        *,
        offset: int,
        limit: int,
        search: str | None,
        product_id: int | None,
        warehouse_id: int | None,
        movement_type: StockMovementType | None,
        created_from: datetime | None,
        created_to: datetime | None,
        sort_order: SortOrder,
    ) -> tuple[list[StockMovement], int]:
        filters = []
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Product.sku.ilike(pattern),
                    Product.name.ilike(pattern),
                    Warehouse.code.ilike(pattern),
                    Warehouse.name.ilike(pattern),
                )
            )
        if product_id is not None:
            filters.append(StockMovement.product_id == product_id)
        if warehouse_id is not None:
            filters.append(StockMovement.warehouse_id == warehouse_id)
        if movement_type is not None:
            filters.append(StockMovement.type == movement_type)
        if created_from is not None:
            filters.append(StockMovement.created_at >= created_from)
        if created_to is not None:
            filters.append(StockMovement.created_at <= created_to)

        base = (
            select(StockMovement)
            .join(StockMovement.product)
            .join(StockMovement.warehouse)
            .where(*filters)
        )
        count_statement = (
            select(func.count())
            .select_from(StockMovement)
            .join(StockMovement.product)
            .join(StockMovement.warehouse)
            .where(*filters)
        )
        ordering = (
            StockMovement.created_at.desc()
            if sort_order == "desc"
            else StockMovement.created_at.asc()
        )
        id_ordering = (
            StockMovement.id.desc() if sort_order == "desc" else StockMovement.id.asc()
        )
        statement = (
            base.options(
                selectinload(StockMovement.product),
                selectinload(StockMovement.warehouse),
                selectinload(StockMovement.creator),
            )
            .order_by(ordering, id_ordering)
            .offset(offset)
            .limit(limit)
        )
        movements = list((await self.session.scalars(statement)).all())
        total = int(await self.session.scalar(count_statement) or 0)
        return movements, total

    async def get_movement_with_details(self, movement_id: int) -> StockMovement | None:
        statement = (
            select(StockMovement)
            .where(StockMovement.id == movement_id)
            .options(
                selectinload(StockMovement.product),
                selectinload(StockMovement.warehouse),
                selectinload(StockMovement.creator),
            )
        )
        return cast(StockMovement | None, await self.session.scalar(statement))

    def add_inventory(self, inventory: Inventory) -> None:
        self.session.add(inventory)

    def add_movement(self, movement: StockMovement) -> None:
        self.session.add(movement)

    def add_movements(self, movements: list[StockMovement]) -> None:
        self.session.add_all(movements)
