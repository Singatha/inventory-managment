from typing import cast

from sqlalchemy import func, or_, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.inventory.models import Inventory, StockMovement
from app.orders.models import Order, OrderItem, OrderStatus
from app.orders.schemas import OrderSortField, SortOrder
from app.products.models import Product
from app.users.models import User
from app.warehouses.models import Warehouse


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_orders(
        self,
        *,
        offset: int,
        limit: int,
        search: str | None,
        order_status: OrderStatus | None,
        created_by: int | None,
        sort_by: OrderSortField,
        sort_order: SortOrder,
    ) -> tuple[list[Order], int]:
        filters = []
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Order.order_number.ilike(pattern),
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                    User.email.ilike(pattern),
                )
            )
        if order_status is not None:
            filters.append(Order.status == order_status)
        if created_by is not None:
            filters.append(Order.created_by == created_by)

        base = select(Order).join(Order.creator).where(*filters)
        count_statement = (
            select(func.count()).select_from(Order).join(Order.creator).where(*filters)
        )
        sort_columns = {
            "order_number": Order.order_number,
            "status": Order.status,
            "created_at": Order.created_at,
            "updated_at": Order.updated_at,
        }
        sort_column = sort_columns[sort_by]
        ordering = sort_column.desc() if sort_order == "desc" else sort_column.asc()
        statement = (
            base.options(
                selectinload(Order.creator),
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.items).selectinload(OrderItem.warehouse),
            )
            .order_by(ordering, Order.id.desc())
            .offset(offset)
            .limit(limit)
        )
        orders = list((await self.session.scalars(statement)).all())
        total = int(await self.session.scalar(count_statement) or 0)
        return orders, total

    async def get_with_details(self, order_id: int) -> Order | None:
        statement = select(Order).where(Order.id == order_id).options(
            selectinload(Order.creator),
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.items).selectinload(OrderItem.warehouse),
        )
        return cast(Order | None, await self.session.scalar(statement))

    async def get_for_update(self, order_id: int) -> Order | None:
        statement = select(Order).where(Order.id == order_id).with_for_update()
        return cast(Order | None, await self.session.scalar(statement))

    async def get_products(self, product_ids: set[int]) -> dict[int, Product]:
        statement = select(Product).where(Product.id.in_(product_ids))
        rows = (await self.session.scalars(statement)).all()
        return {row.id: row for row in rows}

    async def get_warehouses(self, warehouse_ids: set[int]) -> dict[int, Warehouse]:
        rows = (
            await self.session.scalars(select(Warehouse).where(Warehouse.id.in_(warehouse_ids)))
        ).all()
        return {row.id: row for row in rows}

    async def get_inventory_for_update(
        self, pairs: set[tuple[int, int]]
    ) -> dict[tuple[int, int], Inventory]:
        if not pairs:
            return {}
        statement = (
            select(Inventory)
            .where(tuple_(Inventory.product_id, Inventory.warehouse_id).in_(sorted(pairs)))
            .order_by(Inventory.warehouse_id.asc(), Inventory.product_id.asc())
            .with_for_update()
        )
        rows = (await self.session.scalars(statement)).all()
        return {(row.product_id, row.warehouse_id): row for row in rows}

    def add_order(self, order: Order) -> None:
        self.session.add(order)

    def add_movements(self, movements: list[StockMovement]) -> None:
        self.session.add_all(movements)
