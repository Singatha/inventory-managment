"""Index stock movement history.

Revision ID: 20260904_0005
Revises: 20260904_0004
Create Date: 2026-09-04 03:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260904_0005"
down_revision: str | None = "20260904_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_stock_movements_warehouse_id",
        "stock_movements",
        ["warehouse_id"],
        unique=False,
    )
    op.create_index(
        "ix_stock_movements_type", "stock_movements", ["type"], unique=False
    )
    op.create_index(
        "ix_stock_movements_reference",
        "stock_movements",
        ["reference_type", "reference_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_stock_movements_reference", table_name="stock_movements")
    op.drop_index("ix_stock_movements_type", table_name="stock_movements")
    op.drop_index("ix_stock_movements_warehouse_id", table_name="stock_movements")
