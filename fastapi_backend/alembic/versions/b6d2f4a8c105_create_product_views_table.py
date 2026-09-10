"""create product_views table

Revision ID: b6d2f4a8c105
Revises: a9c3e8f1b205
Create Date: 2026-09-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b6d2f4a8c105'
down_revision: Union[str, Sequence[str], None] = 'a9c3e8f1b205'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_views",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("viewed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_product_views_user_id"), "product_views", ["user_id"], unique=False)
    op.create_index(op.f("ix_product_views_product_id"), "product_views", ["product_id"], unique=False)
    op.create_index(op.f("ix_product_views_viewed_at"), "product_views", ["viewed_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_product_views_viewed_at"), table_name="product_views")
    op.drop_index(op.f("ix_product_views_product_id"), table_name="product_views")
    op.drop_index(op.f("ix_product_views_user_id"), table_name="product_views")
    op.drop_table("product_views")