from datetime import UTC, datetime
from secrets import token_hex
from typing import NoReturn

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import AppError
from app.inventory.models import Inventory, StockMovement, StockMovementType
from app.orders.models import Order, OrderItem, OrderStatus
from app.orders.repository import OrderRepository
from app.orders.schemas import (
    OrderCreate,
    OrderListResponse,
    OrderResponse,
    OrderSortField,
    SortOrder,
)
from app.users.models import User, UserRole


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = OrderRepository(session)

    async def create_order(self, data: OrderCreate, *, created_by: int) -> OrderResponse:
        product_ids = {item.product_id for item in data.items}
        warehouse_ids = {item.warehouse_id for item in data.items}
        products = await self.repository.get_products(product_ids)
        warehouses = await self.repository.get_warehouses(warehouse_ids)
        missing_products = sorted(product_ids - products.keys())
        if missing_products:
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="PRODUCT_NOT_FOUND",
                message="One or more requested products do not exist.",
                details={"product_ids": missing_products},
            )
        inactive_products = sorted(
            product_id for product_id, product in products.items() if not product.is_active
        )
        if inactive_products:
            raise AppError(
                status_code=status.HTTP_409_CONFLICT,
                code="PRODUCT_INACTIVE",
                message="Orders cannot contain inactive products.",
                details={"product_ids": inactive_products},
            )
        missing_warehouses = sorted(warehouse_ids - warehouses.keys())
        if missing_warehouses:
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="WAREHOUSE_NOT_FOUND",
                message="One or more requested warehouses do not exist.",
                details={"warehouse_ids": missing_warehouses},
            )

        order = Order(
            order_number=f"SO-{datetime.now(UTC):%Y%m%d}-{token_hex(4).upper()}",
            status=OrderStatus.PENDING,
            created_by=created_by,
            items=[
                OrderItem(
                    product_id=item.product_id,
                    warehouse_id=item.warehouse_id,
                    quantity=item.quantity,
                    unit_price=products[item.product_id].price,
                )
                for item in data.items
            ],
        )
        self.repository.add_order(order)
        try:
            await self.session.flush()
            order_id = order.id
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                status_code=status.HTTP_409_CONFLICT,
                code="ORDER_CONFLICT",
                message="The order could not be created. Please retry.",
            ) from exc
        return await self._reload(order_id)

    async def list_orders(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        order_status: OrderStatus | None,
        created_by: int | None,
        sort_by: OrderSortField,
        sort_order: SortOrder,
    ) -> OrderListResponse:
        orders, total = await self.repository.list_orders(
            offset=(page - 1) * page_size,
            limit=page_size,
            search=search,
            order_status=order_status,
            created_by=created_by,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return OrderListResponse(items=orders, total=total, page=page, page_size=page_size)

    async def get_order(self, order_id: int) -> OrderResponse:
        return OrderResponse.model_validate(await self._get_or_404(order_id))

    async def confirm_order(self, order_id: int, *, actor_id: int) -> OrderResponse:
        order = await self._lock_order(order_id)
        self._require_status(order, OrderStatus.PENDING)
        inventory = await self._lock_inventory(order)
        shortages = [
            self._shortage(item, inventory.get((item.product_id, item.warehouse_id)))
            for item in order.items
            if self._available(inventory.get((item.product_id, item.warehouse_id)))
            < item.quantity
        ]
        if shortages:
            raise AppError(
                status_code=status.HTTP_409_CONFLICT,
                code="INSUFFICIENT_STOCK",
                message="The order cannot be confirmed because stock is insufficient.",
                details={"items": shortages},
            )

        movements = []
        for item in order.items:
            balance = inventory[(item.product_id, item.warehouse_id)]
            balance.quantity_reserved += item.quantity
            movements.append(
                self._movement(item, StockMovementType.RESERVE, -item.quantity, actor_id, order.id)
            )
        self.repository.add_movements(movements)
        order.status = OrderStatus.CONFIRMED
        return await self._commit_transition(order)

    async def process_order(self, order_id: int) -> OrderResponse:
        order = await self._lock_order(order_id)
        self._require_status(order, OrderStatus.CONFIRMED)
        order.status = OrderStatus.PROCESSING
        return await self._commit_transition(order)

    async def ship_order(self, order_id: int, *, actor_id: int) -> OrderResponse:
        order = await self._lock_order(order_id)
        self._require_status(order, OrderStatus.PROCESSING)
        inventory = await self._lock_inventory(order)
        invalid = [
            item
            for item in order.items
            if (balance := inventory.get((item.product_id, item.warehouse_id))) is None
            or balance.quantity_reserved < item.quantity
            or balance.quantity_on_hand < item.quantity
        ]
        if invalid:
            raise AppError(
                status_code=status.HTTP_409_CONFLICT,
                code="RESERVATION_INVALID",
                message="Reserved inventory no longer covers this order.",
                details={"order_item_ids": [item.id for item in invalid]},
            )

        movements = []
        for item in order.items:
            balance = inventory[(item.product_id, item.warehouse_id)]
            balance.quantity_on_hand -= item.quantity
            balance.quantity_reserved -= item.quantity
            movements.append(
                self._movement(item, StockMovementType.SHIPMENT, -item.quantity, actor_id, order.id)
            )
        self.repository.add_movements(movements)
        order.status = OrderStatus.SHIPPED
        return await self._commit_transition(order)

    async def complete_order(self, order_id: int) -> OrderResponse:
        order = await self._lock_order(order_id)
        self._require_status(order, OrderStatus.SHIPPED)
        order.status = OrderStatus.COMPLETED
        return await self._commit_transition(order)

    async def cancel_order(self, order_id: int, *, actor: User) -> OrderResponse:
        order = await self._lock_order(order_id)
        if actor.role == UserRole.EMPLOYEE and (
            order.created_by != actor.id or order.status != OrderStatus.PENDING
        ):
            raise AppError(
                status_code=status.HTTP_403_FORBIDDEN,
                code="INSUFFICIENT_PERMISSIONS",
                message="Employees may only cancel their own pending orders.",
            )
        if order.status not in {
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PROCESSING,
        }:
            self._raise_invalid_transition(order, OrderStatus.CANCELLED)

        if order.status in {OrderStatus.CONFIRMED, OrderStatus.PROCESSING}:
            inventory = await self._lock_inventory(order)
            invalid = [
                item
                for item in order.items
                if (balance := inventory.get((item.product_id, item.warehouse_id))) is None
                or balance.quantity_reserved < item.quantity
            ]
            if invalid:
                raise AppError(
                    status_code=status.HTTP_409_CONFLICT,
                    code="RESERVATION_INVALID",
                    message="Reserved inventory no longer covers this order.",
                    details={"order_item_ids": [item.id for item in invalid]},
                )
            movements = []
            for item in order.items:
                inventory[(item.product_id, item.warehouse_id)].quantity_reserved -= item.quantity
                movements.append(
                    self._movement(
                        item, StockMovementType.RELEASE, item.quantity, actor.id, order.id
                    )
                )
            self.repository.add_movements(movements)
        order.status = OrderStatus.CANCELLED
        return await self._commit_transition(order)

    async def _lock_order(self, order_id: int) -> Order:
        order = await self.repository.get_for_update(order_id)
        if order is None:
            self._raise_not_found()
        detailed = await self.repository.get_with_details(order_id)
        if detailed is None:
            self._raise_not_found()
        return detailed

    async def _lock_inventory(self, order: Order) -> dict[tuple[int, int], Inventory]:
        pairs = {(item.product_id, item.warehouse_id) for item in order.items}
        return await self.repository.get_inventory_for_update(pairs)

    async def _get_or_404(self, order_id: int) -> Order:
        order = await self.repository.get_with_details(order_id)
        if order is None:
            self._raise_not_found()
        return order

    async def _reload(self, order_id: int) -> OrderResponse:
        order = await self.repository.get_with_details(order_id)
        if order is None:
            raise RuntimeError("Committed order could not be reloaded.")
        return OrderResponse.model_validate(order)

    async def _commit_transition(self, order: Order) -> OrderResponse:
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                status_code=status.HTTP_409_CONFLICT,
                code="ORDER_CONFLICT",
                message="The order changed concurrently. Please retry.",
            ) from exc
        return await self._reload(order.id)

    @staticmethod
    def _require_status(order: Order, expected: OrderStatus) -> None:
        if order.status != expected:
            OrderService._raise_invalid_transition(order, expected)

    @staticmethod
    def _raise_invalid_transition(order: Order, target: OrderStatus) -> NoReturn:
        raise AppError(
            status_code=status.HTTP_409_CONFLICT,
            code="ORDER_TRANSITION_INVALID",
            message=(
                f"Order {order.order_number} cannot move from "
                f"{order.status.value} to {target.value}."
            ),
            details={"current_status": order.status.value, "target_status": target.value},
        )

    @staticmethod
    def _raise_not_found() -> NoReturn:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ORDER_NOT_FOUND",
            message="The requested order does not exist.",
        )

    @staticmethod
    def _available(inventory: Inventory | None) -> int:
        return inventory.available_quantity if inventory is not None else 0

    @staticmethod
    def _shortage(item: OrderItem, inventory: Inventory | None) -> dict[str, int]:
        return {
            "order_item_id": item.id,
            "product_id": item.product_id,
            "warehouse_id": item.warehouse_id,
            "requested_quantity": item.quantity,
            "available_quantity": OrderService._available(inventory),
        }

    @staticmethod
    def _movement(
        item: OrderItem,
        movement_type: StockMovementType,
        quantity: int,
        actor_id: int,
        order_id: int,
    ) -> StockMovement:
        return StockMovement(
            product_id=item.product_id,
            warehouse_id=item.warehouse_id,
            type=movement_type,
            quantity=quantity,
            reference_type="ORDER",
            reference_id=order_id,
            notes=None,
            created_by=actor_id,
        )
