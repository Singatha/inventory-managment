from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_roles
from app.core.database import get_session
from app.products.models import Product
from app.products.schemas import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductSortField,
    ProductUpdate,
    SortOrder,
)
from app.products.service import ProductService
from app.users.models import User, UserRole

router = APIRouter(prefix="/products", tags=["products"])
Session = Annotated[AsyncSession, Depends(get_session)]
AuthenticatedUser = Annotated[User, Depends(get_current_user)]
ProductManager = Annotated[
    User, Depends(require_roles(UserRole.ADMIN, UserRole.WAREHOUSE_MANAGER))
]


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(data: ProductCreate, _: ProductManager, session: Session) -> Product:
    return await ProductService(session).create_product(data)


@router.get("", response_model=ProductListResponse)
async def list_products(
    _: AuthenticatedUser,
    session: Session,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=200)] = None,
    category: Annotated[str | None, Query(max_length=100)] = None,
    is_active: bool | None = None,
    sort_by: ProductSortField = "name",
    sort_order: SortOrder = "asc",
) -> ProductListResponse:
    products, total = await ProductService(session).list_products(
        page=page,
        page_size=page_size,
        search=search,
        category=category,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return ProductListResponse(items=products, total=total, page=page, page_size=page_size)


@router.get("/categories", response_model=list[str])
async def list_categories(_: AuthenticatedUser, session: Session) -> list[str]:
    return await ProductService(session).list_categories()


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, _: AuthenticatedUser, session: Session) -> Product:
    return await ProductService(session).get_product(product_id)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int, changes: ProductUpdate, _: ProductManager, session: Session
) -> Product:
    return await ProductService(session).update_product(product_id, changes)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int, _: ProductManager, session: Session
) -> Response:
    await ProductService(session).deactivate_product(product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

