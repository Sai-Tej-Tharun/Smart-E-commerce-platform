"""add RETURNED order status and return-related notification types

Revision ID: f2a7d6e1c934
Revises: e5f9a2c4b813
Create Date: 2026-09-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f2a7d6e1c934'
down_revision: Union[str, Sequence[str], None] = 'e5f9a2c4b813'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # orders.order_status: widen to add RETURNED (Admin-side Refund
    # Processing milestone — see models/order.py's OrderStatus).
    op.alter_column(
        "orders",
        "order_status",
        existing_type=sa.Enum("PENDING", "PAID", "SHIPPED", "DELIVERED", "CANCELLED", "RETURN_REQUESTED", name="orderstatus"),
        type_=sa.Enum("PENDING", "PAID", "SHIPPED", "DELIVERED", "CANCELLED", "RETURN_REQUESTED", "RETURNED", name="orderstatus"),
        existing_nullable=False,
    )

    # notifications.type: widen to add the three new return/refund events.
    op.alter_column(
        "notifications",
        "type",
        existing_type=sa.Enum(
            "ORDER_CONFIRMED", "PAYMENT_SUCCESSFUL", "PAYMENT_FAILED", "ORDER_SHIPPED", "ORDER_DELIVERED",
            name="notificationtype",
        ),
        type_=sa.Enum(
            "ORDER_CONFIRMED", "PAYMENT_SUCCESSFUL", "PAYMENT_FAILED", "ORDER_SHIPPED", "ORDER_DELIVERED",
            "RETURN_APPROVED", "RETURN_REJECTED", "REFUND_COMPLETED",
            name="notificationtype",
        ),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "notifications",
        "type",
        existing_type=sa.Enum(
            "ORDER_CONFIRMED", "PAYMENT_SUCCESSFUL", "PAYMENT_FAILED", "ORDER_SHIPPED", "ORDER_DELIVERED",
            "RETURN_APPROVED", "RETURN_REJECTED", "REFUND_COMPLETED",
            name="notificationtype",
        ),
        type_=sa.Enum(
            "ORDER_CONFIRMED", "PAYMENT_SUCCESSFUL", "PAYMENT_FAILED", "ORDER_SHIPPED", "ORDER_DELIVERED",
            name="notificationtype",
        ),
        existing_nullable=False,
    )
    op.alter_column(
        "orders",
        "order_status",
        existing_type=sa.Enum("PENDING", "PAID", "SHIPPED", "DELIVERED", "CANCELLED", "RETURN_REQUESTED", "RETURNED", name="orderstatus"),
        type_=sa.Enum("PENDING", "PAID", "SHIPPED", "DELIVERED", "CANCELLED", "RETURN_REQUESTED", name="orderstatus"),
        existing_nullable=False,
    )