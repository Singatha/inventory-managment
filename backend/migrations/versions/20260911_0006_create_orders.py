"""create orders and order items

Revision ID: 20260911_0006
Revises: 20260904_0005
Create Date: 2026-09-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260911_0006"
down_revision: str | None = "20260904_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

order_status = postgresql.ENUM(
    "PENDING",
    "CONFIRMED",
    "PROCESSING",
    "SHIPPED",
    "COMPLETED",
    "CANCELLED",
    name="order_status",
    create_type=False,
)


def upgrade() -> None:
    order_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "orders",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("order_number", sa.String(length=40), nullable=False),
        sa.Column("status", order_status, nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_number"),
    )
    op.create_index("ix_orders_status", "orders", ["status"], unique=False)
    op.create_index("ix_orders_created_by", "orders", ["created_by"], unique=False)
    op.create_index("ix_orders_created_at", "orders", ["created_at"], unique=False)
    op.create_table(
        "order_items",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("warehouse_id", sa.BigInteger(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price_non_negative"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "order_id", "product_id", "warehouse_id", name="uq_order_item_product_warehouse"
        ),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"], unique=False)
    op.create_index("ix_order_items_product_id", "order_items", ["product_id"], unique=False)
    op.create_index(
        "ix_order_items_warehouse_id", "order_items", ["warehouse_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_order_items_warehouse_id", table_name="order_items")
    op.drop_index("ix_order_items_product_id", table_name="order_items")
    op.drop_index("ix_order_items_order_id", table_name="order_items")
    op.drop_table("order_items")
    op.drop_index("ix_orders_created_at", table_name="orders")
    op.drop_index("ix_orders_created_by", table_name="orders")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_table("orders")
    order_status.drop(op.get_bind(), checkfirst=True)
