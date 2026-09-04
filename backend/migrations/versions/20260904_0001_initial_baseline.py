"""Initial schema baseline.

Revision ID: 20260904_0001
Revises:
Create Date: 2026-09-04 00:00:00
"""

from collections.abc import Sequence

revision: str = "20260904_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Establish an empty baseline; domain tables arrive in later milestones."""


def downgrade() -> None:
    """Remove the empty baseline."""

