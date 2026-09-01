"""create notifications table

Revision ID: d8e1f5a3c720
Revises: c7b2e4a91f05
Create Date: 2026-08-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd8e1f5a3c720'
down_revision: Union[str, Sequence[str], None] = 'c7b2e4a91f05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "ORDER_CONFIRMED", "PAYMENT_SUCCESSFUL", "PAYMENT_FAILED", "ORDER_SHIPPED", "ORDER_DELIVERED",
                name="notificationtype",
            ),
            nullable=False,
        ),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("read_status", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_table("notifications")
    sa.Enum(name="notificationtype").drop(op.get_bind(), checkfirst=True)