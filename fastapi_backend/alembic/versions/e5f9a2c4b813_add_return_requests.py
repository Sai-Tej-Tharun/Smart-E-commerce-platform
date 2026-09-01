"""add delivered_at, RETURN_REQUESTED status, return_requests table

Revision ID: e5f9a2c4b813
Revises: d8e1f5a3c720
Create Date: 2026-08-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e5f9a2c4b813'
down_revision: Union[str, Sequence[str], None] = 'd8e1f5a3c720'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- orders: new nullable column ----
    op.add_column("orders", sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True))

    # ---- orders.order_status: widen the MySQL ENUM to add RETURN_REQUESTED ----
    # MySQL has no "ALTER TYPE ADD VALUE" like Postgres — the column has to
    # be redefined with the full new list of allowed values. Existing rows
    # keep their current value untouched; this only adds a new option.
    op.alter_column(
        "orders",
        "order_status",
        existing_type=sa.Enum("PENDING", "PAID", "SHIPPED", "DELIVERED", "CANCELLED", name="orderstatus"),
        type_=sa.Enum("PENDING", "PAID", "SHIPPED", "DELIVERED", "CANCELLED", "RETURN_REQUESTED", name="orderstatus"),
        existing_nullable=False,
    )

    # ---- return_requests: new table ----
    op.create_table(
        "return_requests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reason", sa.String(length=200), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("PENDING", "APPROVED", "REJECTED", name="returnrequeststatus"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_return_requests_order_id"), "return_requests", ["order_id"], unique=False)
    op.create_index(op.f("ix_return_requests_user_id"), "return_requests", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_return_requests_user_id"), table_name="return_requests")
    op.drop_index(op.f("ix_return_requests_order_id"), table_name="return_requests")
    op.drop_table("return_requests")
    sa.Enum(name="returnrequeststatus").drop(op.get_bind(), checkfirst=True)

    op.alter_column(
        "orders",
        "order_status",
        existing_type=sa.Enum("PENDING", "PAID", "SHIPPED", "DELIVERED", "CANCELLED", "RETURN_REQUESTED", name="orderstatus"),
        type_=sa.Enum("PENDING", "PAID", "SHIPPED", "DELIVERED", "CANCELLED", name="orderstatus"),
        existing_nullable=False,
    )
    op.drop_column("orders", "delivered_at")