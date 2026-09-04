"""Create warehouses, inventory, and stock movements.

Revision ID: 20260904_0004
Revises: 20260904_0003
Create Date: 2026-09-04 02:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260904_0004"
down_revision: str | None = "20260904_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

stock_movement_type = postgresql.ENUM(
    "RECEIVE",
    "ADJUSTMENT",
    "RESERVE",
    "RELEASE",
    "SHIPMENT",
    "TRANSFER_IN",
    "TRANSFER_OUT",
    "RETURN",
    name="stock_movement_type",
    create_type=False,
)


def upgrade() -> None:
    stock_movement_type.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "warehouses",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("location", sa.String(length=500), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "inventory",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("warehouse_id", sa.BigInteger(), nullable=False),
        sa.Column("quantity_on_hand", sa.Integer(), nullable=False),
        sa.Column("quantity_reserved", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "quantity_on_hand >= 0", name="ck_inventory_quantity_on_hand_non_negative"
        ),
        sa.CheckConstraint(
            "quantity_reserved >= 0", name="ck_inventory_quantity_reserved_non_negative"
        ),
        sa.CheckConstraint(
            "quantity_reserved <= quantity_on_hand",
            name="ck_inventory_reserved_not_above_on_hand",
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "product_id", "warehouse_id", name="uq_inventory_product_warehouse"
        ),
    )
    op.create_index("ix_inventory_product_id", "inventory", ["product_id"], unique=False)
    op.create_index(
        "ix_inventory_warehouse_id", "inventory", ["warehouse_id"], unique=False
    )
    op.create_table(
        "stock_movements",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("warehouse_id", sa.BigInteger(), nullable=False),
        sa.Column("type", stock_movement_type, nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reference_type", sa.String(length=50), nullable=True),
        sa.Column("reference_id", sa.BigInteger(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("quantity <> 0", name="ck_stock_movements_quantity_non_zero"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_stock_movements_created_at", "stock_movements", ["created_at"], unique=False
    )
    op.create_index(
        "ix_stock_movements_product_warehouse",
        "stock_movements",
        ["product_id", "warehouse_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_stock_movements_product_warehouse", table_name="stock_movements")
    op.drop_index("ix_stock_movements_created_at", table_name="stock_movements")
    op.drop_table("stock_movements")
    op.drop_index("ix_inventory_warehouse_id", table_name="inventory")
    op.drop_index("ix_inventory_product_id", table_name="inventory")
    op.drop_table("inventory")
    op.drop_table("warehouses")
    stock_movement_type.drop(op.get_bind(), checkfirst=True)
