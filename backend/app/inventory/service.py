from datetime import UTC, datetime

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import AppError
from app.inventory.models import Inventory, StockMovement, StockMovementType
from app.inventory.repository import InventoryRepository
from app.inventory.schemas import (
    InventoryListResponse,
    InventoryOperationResponse,
    InventoryResponse,
    InventorySortField,
    SortOrder,
    StockAdjustment,
    StockMovementDetailResponse,
    StockMovementListResponse,
    StockMovementResponse,
    StockReceive,
    StockTransfer,
    StockTransferResponse,
)
from app.products.models import Product
from app.warehouses.models import Warehouse


class InventoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = InventoryRepository(session)

    async def list_inventory(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        product_id: int | None,
        warehouse_id: int | None,
        low_stock: bool | None,
        sort_by: InventorySortField,
        sort_order: SortOrder,
    ) -> InventoryListResponse:
        items, total, on_hand, reserved, low_stock_count = (
            await self.repository.list_inventory(
                offset=(page - 1) * page_size,
                limit=page_size,
                search=search,
                product_id=product_id,
                warehouse_id=warehouse_id,
                low_stock=low_stock,
                sort_by=sort_by,
                sort_order=sort_order,
            )
        )
        return InventoryListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_quantity_on_hand=on_hand,
            total_quantity_reserved=reserved,
            total_available_quantity=on_hand - reserved,
            low_stock_count=low_stock_count,
        )

    async def receive_stock(
        self, data: StockReceive, *, created_by: int
    ) -> InventoryOperationResponse:
        await self._require_product(data.product_id)
        await self._require_warehouse(data.warehouse_id)
        inventory = await self.repository.get_for_update(data.product_id, data.warehouse_id)
        if inventory is None:
            inventory = Inventory(
                product_id=data.product_id,
                warehouse_id=data.warehouse_id,
                quantity_on_hand=0,
                quantity_reserved=0,
            )
            self.repository.add_inventory(inventory)
        inventory.quantity_on_hand += data.quantity
        movement = StockMovement(
            product_id=data.product_id,
            warehouse_id=data.warehouse_id,
            type=StockMovementType.RECEIVE,
            quantity=data.quantity,
            reference_type=None,
            reference_id=None,
            notes=data.notes,
            created_by=created_by,
        )
        return await self._commit_change(inventory, movement)

    async def adjust_stock(
        self, data: StockAdjustment, *, created_by: int
    ) -> InventoryOperationResponse:
        await self._require_product(data.product_id)
        await self._require_warehouse(data.warehouse_id)
        inventory = await self.repository.get_for_update(data.product_id, data.warehouse_id)
        if inventory is None:
            inventory = Inventory(
                product_id=data.product_id,
                warehouse_id=data.warehouse_id,
                quantity_on_hand=0,
                quantity_reserved=0,
            )
            self.repository.add_inventory(inventory)

        adjusted_quantity = inventory.quantity_on_hand + data.quantity
        if adjusted_quantity < inventory.quantity_reserved:
            raise AppError(
                status_code=status.HTTP_409_CONFLICT,
                code="INSUFFICIENT_STOCK",
                message="The adjustment would reduce stock below the reserved quantity.",
                details={
                    "quantity_on_hand": inventory.quantity_on_hand,
                    "quantity_reserved": inventory.quantity_reserved,
                    "requested_adjustment": data.quantity,
                },
            )
        inventory.quantity_on_hand = adjusted_quantity
        movement = StockMovement(
            product_id=data.product_id,
            warehouse_id=data.warehouse_id,
            type=StockMovementType.ADJUSTMENT,
            quantity=data.quantity,
            reference_type=None,
            reference_id=None,
            notes=data.reason,
            created_by=created_by,
        )
        return await self._commit_change(inventory, movement)

    async def transfer_stock(
        self, data: StockTransfer, *, created_by: int
    ) -> StockTransferResponse:
        await self._require_product(data.product_id)
        await self._require_warehouse(data.source_warehouse_id)
        await self._require_warehouse(data.destination_warehouse_id)
        ordered_warehouse_ids = (
            (data.source_warehouse_id, data.destination_warehouse_id)
            if data.source_warehouse_id < data.destination_warehouse_id
            else (data.destination_warehouse_id, data.source_warehouse_id)
        )
        rows = await self.repository.get_transfer_rows_for_update(
            data.product_id, ordered_warehouse_ids
        )
        source = rows.get(data.source_warehouse_id)
        available_quantity = source.available_quantity if source is not None else 0
        if source is None or available_quantity < data.quantity:
            raise AppError(
                status_code=status.HTTP_409_CONFLICT,
                code="INSUFFICIENT_STOCK",
                message="The source warehouse does not have enough available stock.",
                details={
                    "available_quantity": available_quantity,
                    "requested_quantity": data.quantity,
                },
            )

        destination = rows.get(data.destination_warehouse_id)
        if destination is None:
            destination = Inventory(
                product_id=data.product_id,
                warehouse_id=data.destination_warehouse_id,
                quantity_on_hand=0,
                quantity_reserved=0,
            )
            self.repository.add_inventory(destination)

        source.quantity_on_hand -= data.quantity
        destination.quantity_on_hand += data.quantity
        transfer_out = StockMovement(
            product_id=data.product_id,
            warehouse_id=data.source_warehouse_id,
            type=StockMovementType.TRANSFER_OUT,
            quantity=-data.quantity,
            reference_type="TRANSFER",
            reference_id=None,
            notes=data.notes,
            created_by=created_by,
        )
        self.repository.add_movement(transfer_out)
        try:
            await self.session.flush()
            transfer_out.reference_id = transfer_out.id
            transfer_in = StockMovement(
                product_id=data.product_id,
                warehouse_id=data.destination_warehouse_id,
                type=StockMovementType.TRANSFER_IN,
                quantity=data.quantity,
                reference_type="TRANSFER",
                reference_id=transfer_out.id,
                notes=data.notes,
                created_by=created_by,
            )
            self.repository.add_movement(transfer_in)
            await self.session.flush()
            source_id = source.id
            destination_id = destination.id
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                status_code=status.HTTP_409_CONFLICT,
                code="INVENTORY_CONFLICT",
                message="Inventory changed concurrently. Please retry the transfer.",
            ) from exc

        source_inventory = await self.repository.get_with_details(source_id)
        destination_inventory = await self.repository.get_with_details(destination_id)
        if source_inventory is None or destination_inventory is None:
            raise RuntimeError("Committed transfer inventory could not be reloaded.")
        await self.session.refresh(transfer_out)
        await self.session.refresh(transfer_in)
        return StockTransferResponse(
            source_inventory=InventoryResponse.model_validate(source_inventory),
            destination_inventory=InventoryResponse.model_validate(destination_inventory),
            movements=[
                StockMovementResponse.model_validate(transfer_out),
                StockMovementResponse.model_validate(transfer_in),
            ],
        )

    async def list_stock_movements(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        product_id: int | None,
        warehouse_id: int | None,
        movement_type: StockMovementType | None,
        created_from: datetime | None,
        created_to: datetime | None,
        sort_order: SortOrder,
    ) -> StockMovementListResponse:
        if created_from is not None and created_from.tzinfo is None:
            created_from = created_from.replace(tzinfo=UTC)
        if created_to is not None and created_to.tzinfo is None:
            created_to = created_to.replace(tzinfo=UTC)
        if created_from is not None and created_to is not None and created_from > created_to:
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="INVALID_DATE_RANGE",
                message="The start date must not be after the end date.",
            )
        movements, total = await self.repository.list_movements(
            offset=(page - 1) * page_size,
            limit=page_size,
            search=search,
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type=movement_type,
            created_from=created_from,
            created_to=created_to,
            sort_order=sort_order,
        )
        return StockMovementListResponse(
            items=movements, total=total, page=page, page_size=page_size
        )

    async def get_stock_movement(self, movement_id: int) -> StockMovementDetailResponse:
        movement = await self.repository.get_movement_with_details(movement_id)
        if movement is None:
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="STOCK_MOVEMENT_NOT_FOUND",
                message="The requested stock movement does not exist.",
            )
        return StockMovementDetailResponse.model_validate(movement)

    async def _require_product(self, product_id: int) -> Product:
        product = await self.session.get(Product, product_id)
        if product is None:
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="PRODUCT_NOT_FOUND",
                message="The requested product does not exist.",
            )
        if not product.is_active:
            raise AppError(
                status_code=status.HTTP_409_CONFLICT,
                code="PRODUCT_INACTIVE",
                message="Inventory cannot be changed for an inactive product.",
            )
        return product

    async def _require_warehouse(self, warehouse_id: int) -> Warehouse:
        warehouse = await self.session.get(Warehouse, warehouse_id)
        if warehouse is None:
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="WAREHOUSE_NOT_FOUND",
                message="The requested warehouse does not exist.",
            )
        return warehouse

    async def _commit_change(
        self, inventory: Inventory, movement: StockMovement
    ) -> InventoryOperationResponse:
        self.repository.add_movement(movement)
        try:
            await self.session.flush()
            inventory_id = inventory.id
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                status_code=status.HTTP_409_CONFLICT,
                code="INVENTORY_CONFLICT",
                message="Inventory changed concurrently. Please retry the operation.",
            ) from exc

        refreshed_inventory = await self.repository.get_with_details(inventory_id)
        if refreshed_inventory is None:
            raise RuntimeError("Committed inventory could not be reloaded.")
        await self.session.refresh(movement)
        return InventoryOperationResponse(
            inventory=InventoryResponse.model_validate(refreshed_inventory),
            movement=StockMovementResponse.model_validate(movement),
        )
