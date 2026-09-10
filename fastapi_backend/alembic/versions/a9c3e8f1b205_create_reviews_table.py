"""create reviews table

Revision ID: a9c3e8f1b205
Revises: f2a7d6e1c934
Create Date: 2026-09-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a9c3e8f1b205'
down_revision: Union[str, Sequence[str], None] = 'f2a7d6e1c934'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("PENDING", "APPROVED", "REJECTED", name="reviewstatus"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating_range"),
        sa.UniqueConstraint("user_id", "product_id", name="uq_review_user_product"),
    )
    op.create_index(op.f("ix_reviews_user_id"), "reviews", ["user_id"], unique=False)
    op.create_index(op.f("ix_reviews_product_id"), "reviews", ["product_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reviews_product_id"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_user_id"), table_name="reviews")
    op.drop_table("reviews")
    sa.Enum(name="reviewstatus").drop(op.get_bind(), checkfirst=True)