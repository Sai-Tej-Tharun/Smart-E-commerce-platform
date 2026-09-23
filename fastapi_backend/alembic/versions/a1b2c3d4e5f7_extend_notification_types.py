"""extend notifications.type enum with blog + subscription events

Revision ID: a1b2c3d4e5f7
Revises: f3a4b5c6d7e8
Create Date: 2026-09-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, Sequence[str], None] = 'f3a4b5c6d7e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_OLD_VALUES = (
    "ORDER_CONFIRMED", "PAYMENT_SUCCESSFUL", "PAYMENT_FAILED", "ORDER_SHIPPED",
    "ORDER_DELIVERED", "RETURN_APPROVED", "RETURN_REJECTED", "REFUND_COMPLETED",
)
_NEW_VALUES = _OLD_VALUES + ("BLOG_LIKE_RECEIVED", "BLOG_COMMENT_RECEIVED", "SUBSCRIPTION_ACTIVATED")


def _enum_sql(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in values)


def upgrade() -> None:
    op.execute(f"ALTER TABLE notifications MODIFY COLUMN type ENUM({_enum_sql(_NEW_VALUES)}) NOT NULL")


def downgrade() -> None:
    # Only safe if no rows are currently using the three new values.
    op.execute(f"ALTER TABLE notifications MODIFY COLUMN type ENUM({_enum_sql(_OLD_VALUES)}) NOT NULL")