from decimal import Decimal
from typing import cast

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.products.models import Product
from app.products.schemas import ProductSortField, SortOrder


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, product_id: int) -> Product | None:
        return await self.session.get(Product, product_id)

    async def get_by_sku(self, sku: str) -> Product | None:
        statement = select(Product).where(Product.sku == sku.upper())
        return cast(Product | None, await self.session.scalar(statement))

    async def list_products(
        self,
        *,
        offset: int,
        limit: int,
        search: str | None,
        category: str | None,
        is_active: bool | None,
        sort_by: ProductSortField,
        sort_order: SortOrder,
    ) -> tuple[list[Product], int]:
        filters = []
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(or_(Product.sku.ilike(pattern), Product.name.ilike(pattern)))
        if category:
            filters.append(func.lower(Product.category) == category.strip().lower())
        if is_active is not None:
            filters.append(Product.is_active.is_(is_active))

        statement = select(Product).where(*filters)
        count_statement = select(func.count()).select_from(Product).where(*filters)
        sort_columns = {
            "sku": Product.sku,
            "name": Product.name,
            "category": Product.category,
            "price": Product.price,
            "reorder_level": Product.reorder_level,
            "created_at": Product.created_at,
        }
        sort_column = sort_columns[sort_by]
        ordering = sort_column.desc() if sort_order == "desc" else sort_column.asc()
        statement = statement.order_by(ordering, Product.id.asc()).offset(offset).limit(limit)

        products = list((await self.session.scalars(statement)).all())
        total = await self.session.scalar(count_statement)
        return products, total or 0

    async def list_categories(self) -> list[str]:
        statement: Select[tuple[str]] = (
            select(Product.category).distinct().order_by(Product.category.asc())
        )
        return list((await self.session.scalars(statement)).all())

    def add(self, product: Product) -> None:
        self.session.add(product)

    @staticmethod
    def create_model(
        *,
        sku: str,
        name: str,
        description: str | None,
        category: str,
        price: Decimal,
        reorder_level: int,
        is_active: bool,
    ) -> Product:
        return Product(
            sku=sku,
            name=name,
            description=description,
            category=category,
            price=price,
            reorder_level=reorder_level,
            is_active=is_active,
        )
