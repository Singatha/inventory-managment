from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_roles
from app.core.database import get_session
from app.users.models import User, UserRole
from app.warehouses.models import Warehouse
from app.warehouses.schemas import (
    SortOrder,
    WarehouseCreate,
    WarehouseListResponse,
    WarehouseResponse,
    WarehouseSortField,
    WarehouseUpdate,
)
from app.warehouses.service import WarehouseService

router = APIRouter(prefix="/warehouses", tags=["warehouses"])
Session = Annotated[AsyncSession, Depends(get_session)]
AuthenticatedUser = Annotated[User, Depends(get_current_user)]
WarehouseManager = Annotated[
    User, Depends(require_roles(UserRole.ADMIN, UserRole.WAREHOUSE_MANAGER))
]


@router.post("", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    data: WarehouseCreate, _: WarehouseManager, session: Session
) -> Warehouse:
    return await WarehouseService(session).create_warehouse(data)


@router.get("", response_model=WarehouseListResponse)
async def list_warehouses(
    _: AuthenticatedUser,
    session: Session,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=500)] = None,
    sort_by: WarehouseSortField = "name",
    sort_order: SortOrder = "asc",
) -> WarehouseListResponse:
    warehouses, total = await WarehouseService(session).list_warehouses(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return WarehouseListResponse(
        items=warehouses, total=total, page=page, page_size=page_size
    )


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(
    warehouse_id: int, _: AuthenticatedUser, session: Session
) -> Warehouse:
    return await WarehouseService(session).get_warehouse(warehouse_id)


@router.put("/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: int,
    changes: WarehouseUpdate,
    _: WarehouseManager,
    session: Session,
) -> Warehouse:
    return await WarehouseService(session).update_warehouse(warehouse_id, changes)


@router.delete("/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_warehouse(
    warehouse_id: int, _: WarehouseManager, session: Session
) -> Response:
    await WarehouseService(session).delete_warehouse(warehouse_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
