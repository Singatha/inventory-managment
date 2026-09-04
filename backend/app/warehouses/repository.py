from typing import cast

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.inventory.models import Inventory
from app.warehouses.models import Warehouse
from app.warehouses.schemas import SortOrder, WarehouseSortField


class WarehouseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, warehouse_id: int) -> Warehouse | None:
        return await self.session.get(Warehouse, warehouse_id)

    async def list_warehouses(
        self,
        *,
        offset: int,
        limit: int,
        search: str | None,
        sort_by: WarehouseSortField,
        sort_order: SortOrder,
    ) -> tuple[list[Warehouse], int]:
        filters = []
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Warehouse.code.ilike(pattern),
                    Warehouse.name.ilike(pattern),
                    Warehouse.location.ilike(pattern),
                )
            )

        statement = select(Warehouse).where(*filters)
        count_statement = select(func.count()).select_from(Warehouse).where(*filters)
        sort_columns = {
            "code": Warehouse.code,
            "name": Warehouse.name,
            "location": Warehouse.location,
            "created_at": Warehouse.created_at,
        }
        sort_column = sort_columns[sort_by]
        ordering = sort_column.desc() if sort_order == "desc" else sort_column.asc()
        statement = statement.order_by(ordering, Warehouse.id.asc()).offset(offset).limit(limit)

        warehouses = list((await self.session.scalars(statement)).all())
        total = await self.session.scalar(count_statement)
        return warehouses, total or 0

    async def get_by_code(self, code: str) -> Warehouse | None:
        statement = select(Warehouse).where(Warehouse.code == code.upper())
        return cast(Warehouse | None, await self.session.scalar(statement))

    async def inventory_count(self, warehouse_id: int) -> int:
        statement = (
            select(func.count())
            .select_from(Inventory)
            .where(Inventory.warehouse_id == warehouse_id)
        )
        return int(await self.session.scalar(statement) or 0)

    def add(self, warehouse: Warehouse) -> None:
        self.session.add(warehouse)

    @staticmethod
    def create_model(*, name: str, code: str, location: str) -> Warehouse:
        return Warehouse(name=name, code=code, location=location)
