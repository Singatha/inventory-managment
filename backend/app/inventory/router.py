from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_roles
from app.core.database import get_session
from app.inventory.models import StockMovementType
from app.inventory.schemas import (
    InventoryListResponse,
    InventoryOperationResponse,
    InventorySortField,
    SortOrder,
    StockAdjustment,
    StockMovementDetailResponse,
    StockMovementListResponse,
    StockReceive,
    StockTransfer,
    StockTransferResponse,
)
from app.inventory.service import InventoryService
from app.users.models import User, UserRole

router = APIRouter(prefix="/inventory", tags=["inventory"])
movement_router = APIRouter(prefix="/stock-movements", tags=["stock movements"])
Session = Annotated[AsyncSession, Depends(get_session)]
AuthenticatedUser = Annotated[User, Depends(get_current_user)]
InventoryManager = Annotated[
    User, Depends(require_roles(UserRole.ADMIN, UserRole.WAREHOUSE_MANAGER))
]


async def _list_inventory(
    session: AsyncSession,
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
    return await InventoryService(session).list_inventory(
        page=page,
        page_size=page_size,
        search=search,
        product_id=product_id,
        warehouse_id=warehouse_id,
        low_stock=low_stock,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("", response_model=InventoryListResponse)
async def list_inventory(
    _: AuthenticatedUser,
    session: Session,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=500)] = None,
    product_id: Annotated[int | None, Query(gt=0)] = None,
    warehouse_id: Annotated[int | None, Query(gt=0)] = None,
    low_stock: bool | None = None,
    sort_by: InventorySortField = "product",
    sort_order: SortOrder = "asc",
) -> InventoryListResponse:
    return await _list_inventory(
        session,
        page=page,
        page_size=page_size,
        search=search,
        product_id=product_id,
        warehouse_id=warehouse_id,
        low_stock=low_stock,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/warehouse/{warehouse_id}", response_model=InventoryListResponse)
async def get_warehouse_inventory(
    warehouse_id: int,
    _: AuthenticatedUser,
    session: Session,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> InventoryListResponse:
    return await _list_inventory(
        session,
        page=page,
        page_size=page_size,
        search=None,
        product_id=None,
        warehouse_id=warehouse_id,
        low_stock=None,
        sort_by="product",
        sort_order="asc",
    )


@router.get("/{product_id}", response_model=InventoryListResponse)
async def get_product_inventory(
    product_id: int,
    _: AuthenticatedUser,
    session: Session,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> InventoryListResponse:
    return await _list_inventory(
        session,
        page=page,
        page_size=page_size,
        search=None,
        product_id=product_id,
        warehouse_id=None,
        low_stock=None,
        sort_by="warehouse",
        sort_order="asc",
    )


@router.post(
    "/receive", response_model=InventoryOperationResponse, status_code=status.HTTP_201_CREATED
)
async def receive_stock(
    data: StockReceive, current_user: InventoryManager, session: Session
) -> InventoryOperationResponse:
    return await InventoryService(session).receive_stock(data, created_by=current_user.id)


@router.post(
    "/adjust", response_model=InventoryOperationResponse, status_code=status.HTTP_201_CREATED
)
async def adjust_stock(
    data: StockAdjustment, current_user: InventoryManager, session: Session
) -> InventoryOperationResponse:
    return await InventoryService(session).adjust_stock(data, created_by=current_user.id)


@router.post(
    "/transfer", response_model=StockTransferResponse, status_code=status.HTTP_201_CREATED
)
async def transfer_stock(
    data: StockTransfer, current_user: InventoryManager, session: Session
) -> StockTransferResponse:
    return await InventoryService(session).transfer_stock(data, created_by=current_user.id)


@movement_router.get("", response_model=StockMovementListResponse)
async def list_stock_movements(
    _: AuthenticatedUser,
    session: Session,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=500)] = None,
    product_id: Annotated[int | None, Query(gt=0)] = None,
    warehouse_id: Annotated[int | None, Query(gt=0)] = None,
    movement_type: StockMovementType | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    sort_order: SortOrder = "desc",
) -> StockMovementListResponse:
    return await InventoryService(session).list_stock_movements(
        page=page,
        page_size=page_size,
        search=search,
        product_id=product_id,
        warehouse_id=warehouse_id,
        movement_type=movement_type,
        created_from=created_from,
        created_to=created_to,
        sort_order=sort_order,
    )


@movement_router.get("/{movement_id}", response_model=StockMovementDetailResponse)
async def get_stock_movement(
    movement_id: int, _: AuthenticatedUser, session: Session
) -> StockMovementDetailResponse:
    return await InventoryService(session).get_stock_movement(movement_id)
