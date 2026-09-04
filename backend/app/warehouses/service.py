from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import AppError
from app.warehouses.models import Warehouse
from app.warehouses.repository import WarehouseRepository
from app.warehouses.schemas import SortOrder, WarehouseCreate, WarehouseSortField, WarehouseUpdate


class WarehouseService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = WarehouseRepository(session)

    async def create_warehouse(self, data: WarehouseCreate) -> Warehouse:
        warehouse = self.repository.create_model(**data.model_dump())
        self.repository.add(warehouse)
        await self._commit_with_unique_code()
        await self.session.refresh(warehouse)
        return warehouse

    async def list_warehouses(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        sort_by: WarehouseSortField,
        sort_order: SortOrder,
    ) -> tuple[list[Warehouse], int]:
        return await self.repository.list_warehouses(
            offset=(page - 1) * page_size,
            limit=page_size,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def get_warehouse(self, warehouse_id: int) -> Warehouse:
        warehouse = await self.repository.get_by_id(warehouse_id)
        if warehouse is None:
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="WAREHOUSE_NOT_FOUND",
                message="The requested warehouse does not exist.",
            )
        return warehouse

    async def update_warehouse(
        self, warehouse_id: int, changes: WarehouseUpdate
    ) -> Warehouse:
        warehouse = await self.get_warehouse(warehouse_id)
        for field, value in changes.model_dump(exclude_unset=True).items():
            setattr(warehouse, field, value)
        await self._commit_with_unique_code()
        await self.session.refresh(warehouse)
        return warehouse

    async def delete_warehouse(self, warehouse_id: int) -> None:
        warehouse = await self.get_warehouse(warehouse_id)
        if await self.repository.inventory_count(warehouse_id):
            raise self._warehouse_in_use_error()
        await self.session.delete(warehouse)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise self._warehouse_in_use_error() from exc

    async def _commit_with_unique_code(self) -> None:
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                status_code=status.HTTP_409_CONFLICT,
                code="WAREHOUSE_CODE_ALREADY_EXISTS",
                message="A warehouse with this code already exists.",
            ) from exc

    @staticmethod
    def _warehouse_in_use_error() -> AppError:
        return AppError(
            status_code=status.HTTP_409_CONFLICT,
            code="WAREHOUSE_IN_USE",
            message="A warehouse with inventory history cannot be deleted.",
        )
