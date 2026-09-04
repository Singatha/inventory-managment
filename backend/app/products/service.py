from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import AppError
from app.products.models import Product
from app.products.repository import ProductRepository
from app.products.schemas import ProductCreate, ProductSortField, ProductUpdate, SortOrder


class ProductService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ProductRepository(session)

    async def create_product(self, data: ProductCreate) -> Product:
        product = self.repository.create_model(**data.model_dump())
        self.repository.add(product)
        await self._commit_with_unique_sku()
        await self.session.refresh(product)
        return product

    async def list_products(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        category: str | None,
        is_active: bool | None,
        sort_by: ProductSortField,
        sort_order: SortOrder,
    ) -> tuple[list[Product], int]:
        return await self.repository.list_products(
            offset=(page - 1) * page_size,
            limit=page_size,
            search=search,
            category=category,
            is_active=is_active,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def get_product(self, product_id: int) -> Product:
        product = await self.repository.get_by_id(product_id)
        if product is None:
            raise AppError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="PRODUCT_NOT_FOUND",
                message="The requested product does not exist.",
            )
        return product

    async def update_product(self, product_id: int, changes: ProductUpdate) -> Product:
        product = await self.get_product(product_id)
        for field, value in changes.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        await self._commit_with_unique_sku()
        await self.session.refresh(product)
        return product

    async def deactivate_product(self, product_id: int) -> None:
        product = await self.get_product(product_id)
        product.is_active = False
        await self.session.commit()

    async def list_categories(self) -> list[str]:
        return await self.repository.list_categories()

    async def _commit_with_unique_sku(self) -> None:
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                status_code=status.HTTP_409_CONFLICT,
                code="SKU_ALREADY_EXISTS",
                message="A product with this SKU already exists.",
            ) from exc
