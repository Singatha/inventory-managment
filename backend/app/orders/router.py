from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_roles
from app.core.database import get_session
from app.orders.models import OrderStatus
from app.orders.schemas import (
    OrderCreate,
    OrderListResponse,
    OrderResponse,
    OrderSortField,
    SortOrder,
)
from app.orders.service import OrderService
from app.users.models import User, UserRole

router = APIRouter(prefix="/orders", tags=["orders"])
Session = Annotated[AsyncSession, Depends(get_session)]
AuthenticatedUser = Annotated[User, Depends(get_current_user)]
OrderManager = Annotated[
    User, Depends(require_roles(UserRole.ADMIN, UserRole.WAREHOUSE_MANAGER))
]


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate, current_user: AuthenticatedUser, session: Session
) -> OrderResponse:
    return await OrderService(session).create_order(data, created_by=current_user.id)


@router.get("", response_model=OrderListResponse)
async def list_orders(
    _: AuthenticatedUser,
    session: Session,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=200)] = None,
    order_status: OrderStatus | None = None,
    created_by: Annotated[int | None, Query(gt=0)] = None,
    sort_by: OrderSortField = "created_at",
    sort_order: SortOrder = "desc",
) -> OrderListResponse:
    return await OrderService(session).list_orders(
        page=page,
        page_size=page_size,
        search=search,
        order_status=order_status,
        created_by=created_by,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int, _: AuthenticatedUser, session: Session
) -> OrderResponse:
    return await OrderService(session).get_order(order_id)


@router.post("/{order_id}/confirm", response_model=OrderResponse)
async def confirm_order(
    order_id: int, current_user: OrderManager, session: Session
) -> OrderResponse:
    return await OrderService(session).confirm_order(order_id, actor_id=current_user.id)


@router.post("/{order_id}/process", response_model=OrderResponse)
async def process_order(
    order_id: int, _: OrderManager, session: Session
) -> OrderResponse:
    return await OrderService(session).process_order(order_id)


@router.post("/{order_id}/ship", response_model=OrderResponse)
async def ship_order(
    order_id: int, current_user: OrderManager, session: Session
) -> OrderResponse:
    return await OrderService(session).ship_order(order_id, actor_id=current_user.id)


@router.post("/{order_id}/complete", response_model=OrderResponse)
async def complete_order(
    order_id: int, _: OrderManager, session: Session
) -> OrderResponse:
    return await OrderService(session).complete_order(order_id)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int, current_user: AuthenticatedUser, session: Session
) -> OrderResponse:
    return await OrderService(session).cancel_order(order_id, actor=current_user)
